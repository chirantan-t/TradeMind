import json, logging
import numpy as np
from fastapi import APIRouter, HTTPException
from app.schemas.backtest import BacktestRequest
from app.core.config import settings
from app.api.routes_predictions import get_global_model
from app.data.loader import load_data
from app.features.builder import build_features
from app.regimes.detector import detect_regimes_rule_based, get_regime_features
from app.backtesting.engine import run_backtest
from app.backtesting.metrics import calculate_metrics
from app.storage.database import save_backtest, get_latest_backtest

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['backtest'])

def generate_live_backtest(symbol: str, initial_capital, transaction_cost, slippage, position_mode):
    gm = get_global_model()
    if not gm:
        return None
        
    model = gm['model']
    fc = gm['feature_cols']
    
    try:
        bench_df, _, _ = load_data('^NSEI')
        df, _, _ = load_data(symbol)
        df, _ = build_features(df, benchmark_df=bench_df)
        df = detect_regimes_rule_based(df)
        df = get_regime_features(df)
    except:
        return None
        
    for c in fc:
        if c not in df.columns:
            df[c] = 0
            
    # For backtest, test on the last 2 years (approx 500 trading days)
    test_df = df.tail(500)
    X = test_df[fc].values
    preds = model.predict(X)
    
    bt = run_backtest(test_df, preds,
                      initial_capital=initial_capital,
                      transaction_cost=transaction_cost,
                      slippage=slippage,
                      position_mode=position_mode)
                      
    metrics = calculate_metrics(bt['equity_curve'], bt['trades'],
                                initial_capital=initial_capital,
                                total_costs=bt['total_transaction_costs'],
                                total_slippage=bt['total_slippage'])
    
    return {'metrics': metrics, 'equity_curve': bt['equity_curve'], 'trades': bt['trades']}

@router.get('/backtest/{symbol}')
def get_backtest(symbol: str):
    # In TradeMind 2.0, since models are global, we generate backtest live for the requested symbol.
    result = generate_live_backtest(symbol, settings.DEFAULT_INITIAL_CAPITAL, settings.DEFAULT_TRANSACTION_COST, settings.DEFAULT_SLIPPAGE, 'long_short')
    
    if not result:
        raise HTTPException(status_code=404, detail='No backtest available. Train global model first.')
        
    return {
        'symbol': symbol,
        'metrics': result['metrics'],
        'config': {
            'initial_capital': settings.DEFAULT_INITIAL_CAPITAL,
            'transaction_cost': settings.DEFAULT_TRANSACTION_COST,
            'slippage': settings.DEFAULT_SLIPPAGE,
            'position_mode': 'long_short',
            'currency': settings.ASSET_CURRENCIES.get(symbol, 'INR'),
        }
    }

@router.get('/backtest/{symbol}/equity')
def get_equity(symbol: str):
    result = generate_live_backtest(symbol, settings.DEFAULT_INITIAL_CAPITAL, settings.DEFAULT_TRANSACTION_COST, settings.DEFAULT_SLIPPAGE, 'long_short')
    if not result:
         raise HTTPException(status_code=404, detail='No backtest available.')
    return {
        'symbol': symbol,
        'equity_curve': result['equity_curve'],
        'trades': result['trades'],
    }

@router.post('/backtest/run')
def run_backtest_endpoint(req: BacktestRequest):
    result = generate_live_backtest(req.symbol, req.initial_capital, req.transaction_cost, req.slippage, req.position_mode)
    if not result:
        raise HTTPException(status_code=404, detail='Failed to run backtest.')
        
    save_backtest({
        'run_id': 'GLOBAL', 'symbol': req.symbol,
        'initial_capital': req.initial_capital,
        'transaction_cost': req.transaction_cost,
        'slippage': req.slippage, 'position_mode': req.position_mode,
        'metrics': result['metrics'], 'equity_curve': result['equity_curve']})
        
    return {
        'metrics': result['metrics'], 'equity_curve': result['equity_curve'],
        'trades': result['trades'],
        'config': {'initial_capital': req.initial_capital,
                   'transaction_cost': req.transaction_cost,
                   'slippage': req.slippage, 'position_mode': req.position_mode,
                   'currency': settings.ASSET_CURRENCIES.get(req.symbol, 'INR')}}

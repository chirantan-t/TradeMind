import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/api/routes_models.py', """import json, logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.core.pipeline import get_cache, load_cached_model
from app.storage.database import get_latest_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['models'])

@router.get('/models/{symbol}/metrics')
def model_metrics(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache:
        raise HTTPException(status_code=404, detail='No trained model.')
    mr = cache.get('model_results', {})
    models = mr.get('models', mr)
    result = {}
    for name, data in models.items():
        if isinstance(data, dict):
            if data.get('status') == 'success' or 'val' in data or 'val_metrics' in data:
                result[name] = {
                    'name': name,
                    'val_metrics': data.get('val_metrics', data.get('val', {})),
                    'test_metrics': data.get('test_metrics', data.get('test', {})),
                    'train_time': data.get('train_time', 0),
                    'status': data.get('status', 'success'),
                }
    return {'symbol': symbol, 'models': result,
            'best_model': cache.get('model_name', ''),
            'feature_count': len(cache.get('feature_cols', []))}

@router.get('/models/{symbol}/comparison')
def model_comparison(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache:
        raise HTTPException(status_code=404, detail='No trained model.')
    mr = cache.get('model_results', {})
    models = mr.get('models', mr)
    si = cache.get('split_info', {})
    ti = cache.get('target_info', {})
    bt = cache.get('bt_metrics', {})
    return {
        'symbol': symbol, 'models': models,
        'best_model': cache.get('model_name', ''),
        'split_info': si, 'target_info': ti,
        'backtest_metrics': bt,
        'feature_cols': cache.get('feature_cols', [])[:20],
    }

@router.get('/features/{symbol}')
def get_features(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache:
        raise HTTPException(status_code=404, detail='No data available.')
    fc = cache.get('feature_cols', [])
    df = cache.get('df')
    preview = []
    if df is not None and len(df) > 0:
        last = df.iloc[-1]
        for f in fc[:30]:
            try:
                preview.append({'feature': f, 'value': round(float(last[f]), 6)})
            except: pass
    return {'symbol': symbol, 'feature_count': len(fc),
            'features': fc, 'preview': preview}
""")

w('app/api/routes_backtest.py', """import json, logging
import numpy as np
from fastapi import APIRouter, HTTPException
from app.schemas.backtest import BacktestRequest
from app.core.pipeline import get_cache, load_cached_model
from app.core.config import settings
from app.backtesting.engine import run_backtest
from app.backtesting.metrics import calculate_metrics
from app.storage.database import save_backtest, get_latest_backtest

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['backtest'])

@router.get('/backtest/{symbol}')
def get_backtest(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if cache and cache.get('bt_metrics'):
        return {
            'symbol': symbol,
            'metrics': cache['bt_metrics'],
            'config': {
                'initial_capital': settings.DEFAULT_INITIAL_CAPITAL,
                'transaction_cost': settings.DEFAULT_TRANSACTION_COST,
                'slippage': settings.DEFAULT_SLIPPAGE,
                'position_mode': 'long_short',
                'currency': settings.ASSET_CURRENCIES.get(symbol, 'USD'),
            }
        }
    bt = get_latest_backtest(symbol)
    if bt:
        return {
            'symbol': symbol,
            'metrics': json.loads(bt.get('metrics_json', '{}')),
            'config': {
                'initial_capital': bt.get('initial_capital', 100000),
                'transaction_cost': bt.get('transaction_cost', 0.001),
                'slippage': bt.get('slippage', 0.0005),
                'position_mode': bt.get('position_mode', 'long_short'),
                'currency': settings.ASSET_CURRENCIES.get(symbol, 'USD'),
            }
        }
    raise HTTPException(status_code=404, detail='No backtest available. Train models first.')

@router.get('/backtest/{symbol}/equity')
def get_equity(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if cache and cache.get('backtest'):
        bt = cache['backtest']
        return {
            'symbol': symbol,
            'equity_curve': bt.get('equity_curve', []),
            'trades': bt.get('trades', []),
        }
    bt = get_latest_backtest(symbol)
    if bt:
        return {
            'symbol': symbol,
            'equity_curve': json.loads(bt.get('equity_json', '[]')),
            'trades': [],
        }
    raise HTTPException(status_code=404, detail='No backtest available.')

@router.post('/backtest/run')
def run_backtest_endpoint(req: BacktestRequest):
    cache = get_cache(req.symbol) or load_cached_model(req.symbol)
    if not cache or not cache.get('model'):
        raise HTTPException(status_code=404, detail='No trained model. Train first.')
    model = cache['model']
    fc = cache['feature_cols']
    test_df = cache.get('test_df')
    if test_df is None or len(test_df) == 0:
        raise HTTPException(status_code=400, detail='No test data available.')
    X = test_df[fc].values
    preds = model.predict(X)
    bt = run_backtest(test_df, preds,
                      initial_capital=req.initial_capital,
                      transaction_cost=req.transaction_cost,
                      slippage=req.slippage,
                      position_mode=req.position_mode)
    metrics = calculate_metrics(bt['equity_curve'], bt['trades'],
                                initial_capital=req.initial_capital,
                                total_costs=bt['total_transaction_costs'],
                                total_slippage=bt['total_slippage'])
    # Update cache
    cache['backtest'] = bt
    cache['bt_metrics'] = metrics
    save_backtest({
        'run_id': cache.get('run_id', ''), 'symbol': req.symbol,
        'initial_capital': req.initial_capital,
        'transaction_cost': req.transaction_cost,
        'slippage': req.slippage, 'position_mode': req.position_mode,
        'metrics': metrics, 'equity_curve': bt['equity_curve']})
    return {
        'metrics': metrics, 'equity_curve': bt['equity_curve'],
        'trades': bt['trades'],
        'config': {'initial_capital': req.initial_capital,
                   'transaction_cost': req.transaction_cost,
                   'slippage': req.slippage, 'position_mode': req.position_mode,
                   'currency': settings.ASSET_CURRENCIES.get(req.symbol, 'USD')}}
""")

print('Model & Backtest routes done')
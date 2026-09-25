import json, logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.core.pipeline import get_cache, load_cached_model
from app.api.routes_predictions import get_global_model
from app.data.loader import load_data
from app.features.builder import build_features
from app.regimes.detector import detect_regimes_rule_based, get_regime_features
from app.storage.database import get_latest_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['models'])

@router.get('/models/{symbol}/metrics')
def model_metrics(symbol: str):
    # For TradeMind 2.0, model metrics come from the GLOBAL training run
    global_run = get_latest_run('GLOBAL')
    if not global_run:
        raise HTTPException(status_code=404, detail='No global trained model.')
        
    metrics = json.loads(global_run.get('metrics_json', '{}'))
    result = {}
    for name, data in metrics.items():
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
            'best_model': global_run.get('best_model', ''),
            'feature_count': global_run.get('feature_count', 0)}

@router.get('/models/{symbol}/comparison')
def model_comparison(symbol: str):
    global_run = get_latest_run('GLOBAL')
    if not global_run:
        raise HTTPException(status_code=404, detail='No global trained model.')
        
    metrics = json.loads(global_run.get('metrics_json', '{}'))
    gm = get_global_model()
    fc = gm['feature_cols'] if gm else []
    
    return {
        'symbol': symbol, 'models': metrics,
        'best_model': global_run.get('best_model', ''),
        'split_info': {}, # Obsolete in pooled V2
        'target_info': {}, 
        'backtest_metrics': {}, # Real backtest happens live now
        'feature_cols': fc[:20],
    }

@router.get('/features/{symbol}')
def get_features(symbol: str):
    gm = get_global_model()
    if not gm:
        raise HTTPException(status_code=404, detail='No data available.')
        
    fc = gm['feature_cols']
    preview = []
    
    try:
        bench_df, _, _ = load_data('^NSEI')
        df, _, _ = load_data(symbol)
        df, _ = build_features(df, benchmark_df=bench_df)
        df = detect_regimes_rule_based(df)
        df = get_regime_features(df)
        last = df.iloc[-1]
        
        for f in fc[:30]:
            try:
                preview.append({'feature': f, 'value': round(float(last.get(f, 0)), 6)})
            except: pass
    except:
        pass
        
    return {'symbol': symbol, 'feature_count': len(fc),
            'features': fc, 'preview': preview}

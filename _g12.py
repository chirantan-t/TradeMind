import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/api/routes_training.py', """import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.training import TrainRequest
from app.core.pipeline import run_training_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['training'])

# Track training status
_training_status = {}

@router.post('/train')
def train_models(req: TrainRequest):
    try:
        result = run_training_pipeline(
            symbol=req.symbol, horizon=req.horizon,
            threshold=req.threshold, train_ratio=req.train_ratio,
            val_ratio=req.validation_ratio, use_regime=req.use_regime)
        return result
    except Exception as e:
        logger.error(f'Training failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Training failed: {str(e)}')
""")

w('app/api/routes_predictions.py', """import json, logging
import numpy as np, joblib
from fastapi import APIRouter, HTTPException
from app.core.pipeline import get_cache, load_cached_model
from app.core.config import settings
from app.explainability.shap_explainer import explain_prediction_shap
from app.explainability.feature_importance import (
    get_prediction_contributions, generate_explanation_text,
    get_model_feature_importance)
from app.storage.database import get_predictions

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['predictions'])

LABEL_MAP = {0: 'BUY', 1: 'HOLD', 2: 'SELL'}

@router.get('/prediction/{symbol}')
def get_prediction(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache or not cache.get('model'):
        raise HTTPException(status_code=404, detail='No trained model. Run training first.')
    model = cache['model']
    fc = cache['feature_cols']
    df = cache['df']
    last = df.iloc[-1]
    X = last[fc].values.astype(float).reshape(1, -1)
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    signal = LABEL_MAP.get(int(pred), 'HOLD')
    conf = float(proba.max())

    # Explainability
    drivers = explain_prediction_shap(model, X[0], fc, predicted_class=int(pred))
    if drivers is None:
        drivers = get_prediction_contributions(model, X[0], fc, predicted_class=int(pred))
    top_drivers = (drivers or [])[:10]

    regime = str(last.get('regime_label', 'UNKNOWN'))
    regime_score = float(last.get('regime_score', 0.5))
    vol = float(last.get('volatility_20d', 0))

    explanation = generate_explanation_text(signal, conf, regime, top_drivers)

    return {
        'symbol': symbol, 'date': last['Date'].strftime('%Y-%m-%d'),
        'signal': signal, 'signal_code': int(pred),
        'confidence': round(conf, 4),
        'probabilities': {'BUY': round(float(proba[0]), 4),
                          'HOLD': round(float(proba[1]), 4),
                          'SELL': round(float(proba[2]), 4)},
        'regime': {'label': regime, 'score': round(regime_score, 4),
                   'volatility': round(vol, 4)},
        'model': cache.get('model_name', ''),
        'feature_drivers': top_drivers,
        'explanation': explanation,
    }

@router.get('/signals/{symbol}')
def get_signals(symbol: str, limit: int = 100):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache or not cache.get('model'):
        raise HTTPException(status_code=404, detail='No trained model.')
    model = cache['model']
    fc = cache['feature_cols']
    test_df = cache.get('test_df')
    if test_df is None or len(test_df) == 0:
        return {'symbol': symbol, 'signals': []}
    df_out = test_df.tail(limit)
    X = df_out[fc].values
    preds = model.predict(X)
    probas = model.predict_proba(X)
    signals = []
    for i, (_, row) in enumerate(df_out.iterrows()):
        signals.append({
            'date': row['Date'].strftime('%Y-%m-%d'),
            'signal': LABEL_MAP.get(int(preds[i]), 'HOLD'),
            'confidence': round(float(probas[i].max()), 4),
            'prob_buy': round(float(probas[i][0]), 4),
            'prob_hold': round(float(probas[i][1]), 4),
            'prob_sell': round(float(probas[i][2]), 4),
            'regime': str(row.get('regime_label', '')),
            'regime_score': round(float(row.get('regime_score', 0.5)), 4),
            'close': round(float(row['Close']), 2),
        })
    return {'symbol': symbol, 'signals': signals}

@router.get('/regime/{symbol}')
def get_regime(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache:
        raise HTTPException(status_code=404, detail='No data available.')
    df = cache['df']
    last = df.iloc[-1]
    return {
        'symbol': symbol, 'date': last['Date'].strftime('%Y-%m-%d'),
        'regime': str(last.get('regime_label', 'UNKNOWN')),
        'score': round(float(last.get('regime_score', 0.5)), 4),
        'volatility': round(float(last.get('volatility_20d', 0)), 4),
        'regime_distribution': cache.get('regime_dist', {}),
    }

@router.get('/explain/{symbol}')
def get_explanation(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if not cache or not cache.get('model'):
        raise HTTPException(status_code=404, detail='No trained model.')
    return {
        'symbol': symbol,
        'global_importance': (cache.get('global_importance') or [])[:15],
        'model': cache.get('model_name', ''),
    }
""")

print('Prediction routes done')
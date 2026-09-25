import json, logging
from pathlib import Path
import numpy as np, joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.data.loader import load_data
from app.features.builder import build_features
from app.regimes.detector import detect_regimes_rule_based, get_regime_features
from app.explainability.shap_explainer import explain_prediction_shap
from app.explainability.feature_importance import (
    get_prediction_contributions, generate_explanation_text,
    get_model_feature_importance)

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['predictions'])

LABEL_MAP = {0: 'BUY', 1: 'HOLD', 2: 'SELL'}

# In-memory cache for the global model
_global_model_cache = None

def get_global_model():
    global _global_model_cache
    if _global_model_cache:
        return _global_model_cache
        
    latest_dir = settings.artifacts_path / 'models' / 'global' / 'latest'
    if not latest_dir.exists():
        return None
        
    try:
        model = joblib.load(latest_dir / 'model.joblib')
        fc = joblib.load(latest_dir / 'feature_cols.joblib')
        _global_model_cache = {'model': model, 'feature_cols': fc}
        return _global_model_cache
    except Exception as e:
        logger.error(f"Failed to load global model: {e}")
        return None

@router.get('/prediction/{symbol}')
def get_prediction(symbol: str):
    gm = get_global_model()
    if not gm:
        raise HTTPException(status_code=404, detail='Global model not trained. Please run training first.')
        
    model = gm['model']
    fc = gm['feature_cols']
    
    try:
        # Load benchmark first for context features
        bench_df, _, _ = load_data('^NSEI')
        # Load specific stock data
        df, _, _ = load_data(symbol)
        
        # Build features
        df, _ = build_features(df, benchmark_df=bench_df)
        df = detect_regimes_rule_based(df)
        df = get_regime_features(df)
    except Exception as e:
        logger.exception(f"Failed to process features for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate features for this stock.")

    # Get latest row
    last = df.iloc[-1]
    
    # Ensure all feature columns exist
    for c in fc:
        if c not in df.columns:
            df[c] = 0
            
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
        'model': "TradeMind Global Model",
        'feature_drivers': top_drivers,
        'explanation': explanation,
    }

@router.get('/signals/{symbol}')
def get_signals(symbol: str, limit: int = 100):
    gm = get_global_model()
    if not gm:
        raise HTTPException(status_code=404, detail='Global model not trained.')
        
    model = gm['model']
    fc = gm['feature_cols']
    
    try:
        bench_df, _, _ = load_data('^NSEI')
        df, _, _ = load_data(symbol)
        df, _ = build_features(df, benchmark_df=bench_df)
        df = detect_regimes_rule_based(df)
        df = get_regime_features(df)
    except:
        return {'symbol': symbol, 'signals': []}
        
    for c in fc:
        if c not in df.columns:
            df[c] = 0

    df_out = df.tail(limit)
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
    try:
        df, _, _ = load_data(symbol)
        df = detect_regimes_rule_based(df)
        last = df.iloc[-1]
        dist = df['regime_label'].value_counts().to_dict()
        return {
            'symbol': symbol, 'date': last['Date'].strftime('%Y-%m-%d'),
            'regime': str(last.get('regime_label', 'UNKNOWN')),
            'score': round(float(last.get('regime_score', 0.5)), 4),
            'volatility': round(float(last.get('volatility_20d', 0)), 4),
            'regime_distribution': dist,
        }
    except:
        raise HTTPException(status_code=404, detail='No data available.')

@router.get('/explain/{symbol}')
def get_explanation(symbol: str):
    latest_dir = settings.artifacts_path / 'models' / 'global' / 'latest'
    imp_path = latest_dir / 'feature_importance.json'
    global_imp = []
    if imp_path.exists():
        global_imp = json.loads(imp_path.read_text())
        
    return {
        'symbol': symbol,
        'global_importance': global_imp[:15],
        'model': "TradeMind Global Model",
    }

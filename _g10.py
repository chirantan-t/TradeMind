import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/core/pipeline.py', """import logging, json, uuid, joblib
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd

from app.core.config import settings
from app.data.loader import load_data
from app.features.builder import build_features
from app.features.target import generate_target
from app.data.splitter import chronological_split
from app.regimes.detector import detect_regimes_rule_based, get_regime_features
from app.regimes.clustering import RegimeClusterer
from app.models.trainer import train_all_models
from app.explainability.shap_explainer import explain_prediction_shap, get_global_shap_importance
from app.explainability.feature_importance import (
    get_model_feature_importance, get_prediction_contributions, generate_explanation_text)
from app.backtesting.engine import run_backtest
from app.backtesting.metrics import calculate_metrics
from app.storage.database import save_training_run, save_predictions, save_backtest

logger = logging.getLogger(__name__)

# In-memory cache for loaded models/data
_cache = {}

def run_training_pipeline(symbol='^NSEI', horizon=5, threshold=0.01,
                          train_ratio=0.70, val_ratio=0.15, use_regime=True):
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
    logger.info(f'=== Training Pipeline Start: {symbol} run={run_id} ===')

    # 1. Load data
    logger.info('Step 1: Loading data...')
    df, meta, quality = load_data(symbol)
    logger.info(f'Loaded {len(df)} rows for {symbol}')

    # 2. Build features
    logger.info('Step 2: Building features...')
    df, feature_cols = build_features(df)
    logger.info(f'{len(feature_cols)} features built')

    # 3. Detect regimes
    logger.info('Step 3: Detecting regimes...')
    df = detect_regimes_rule_based(df)
    regime_dist = df['regime_label'].value_counts().to_dict()

    # 4. Add regime features if requested
    if use_regime:
        df = get_regime_features(df)
        regime_feats = ['regime_bull', 'regime_bear', 'regime_sideways']
        feature_cols = feature_cols + [f for f in regime_feats if f not in feature_cols]

    # 5. Generate target
    logger.info('Step 4: Generating target...')
    df, target_info = generate_target(df, horizon=horizon, threshold=threshold)

    # 6. Split data
    logger.info('Step 5: Splitting data...')
    test_ratio = 1.0 - train_ratio - val_ratio
    train_df, val_df, test_df, split_info = chronological_split(
        df, train_ratio=train_ratio, val_ratio=val_ratio, test_ratio=test_ratio)

    # 7. Train K-Means regime clustering (on training data only)
    logger.info('Step 6: Fitting regime clusterer...')
    clusterer = RegimeClusterer(n_clusters=3)
    try:
        clusterer.fit(train_df)
        run_dir = settings.artifacts_path / 'runs' / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        clusterer.save(str(run_dir / 'regime_clusterer.joblib'))
    except Exception as e:
        logger.warning(f'Regime clustering failed: {e}')

    # 8. Train models
    logger.info('Step 7: Training models...')
    model_results = train_all_models(
        train_df, val_df, test_df, feature_cols,
        run_id=run_id, symbol=symbol)

    # 9. Generate predictions and explanations for test set
    logger.info('Step 8: Generating predictions...')
    best_model_name = model_results['best_model']
    run_dir = Path(model_results['run_dir'])

    if best_model_name:
        best_model = joblib.load(run_dir / f'{best_model_name}.joblib')
        X_test = test_df[feature_cols].values
        test_preds = best_model.predict(X_test)
        test_proba = best_model.predict_proba(X_test)

        # Get feature importance
        global_imp = get_global_shap_importance(best_model, X_test, feature_cols)
        if global_imp is None:
            global_imp = get_model_feature_importance(best_model, feature_cols)

        # Save global importance
        if global_imp:
            with open(run_dir / 'feature_importance.json', 'w') as f:
                json.dump(global_imp[:20], f, indent=2)

        # Generate predictions for storage
        label_map = {0: 'BUY', 1: 'HOLD', 2: 'SELL'}
        predictions_to_save = []
        for i in range(len(test_df)):
            pred_class = int(test_preds[i])
            proba = test_proba[i]
            conf = float(proba.max())
            regime_val = test_df.iloc[i].get('regime_label', 'UNKNOWN')
            regime_sc = float(test_df.iloc[i].get('regime_score', 0.5))

            predictions_to_save.append({
                'run_id': run_id, 'symbol': symbol,
                'date': test_df.iloc[i]['Date'].strftime('%Y-%m-%d'),
                'signal': pred_class, 'confidence': conf,
                'prob_buy': float(proba[0]), 'prob_hold': float(proba[1]),
                'prob_sell': float(proba[2]),
                'regime': regime_val, 'regime_score': regime_sc,
                'model_name': best_model_name, 'features': []
            })

        save_predictions(predictions_to_save)

        # 10. Run backtest
        logger.info('Step 9: Running backtest...')
        bt_result = run_backtest(test_df, test_preds,
                                initial_capital=settings.DEFAULT_INITIAL_CAPITAL,
                                transaction_cost=settings.DEFAULT_TRANSACTION_COST,
                                slippage=settings.DEFAULT_SLIPPAGE)
        bt_metrics = calculate_metrics(
            bt_result['equity_curve'], bt_result['trades'],
            initial_capital=settings.DEFAULT_INITIAL_CAPITAL,
            total_costs=bt_result['total_transaction_costs'],
            total_slippage=bt_result['total_slippage'])

        save_backtest({
            'run_id': run_id, 'symbol': symbol,
            'initial_capital': settings.DEFAULT_INITIAL_CAPITAL,
            'transaction_cost': settings.DEFAULT_TRANSACTION_COST,
            'slippage': settings.DEFAULT_SLIPPAGE,
            'position_mode': 'long_short',
            'metrics': bt_metrics, 'equity_curve': bt_result['equity_curve']
        })
    else:
        bt_metrics = {}
        bt_result = {}
        global_imp = []

    # Save training run to DB
    run_data = {
        'run_id': run_id, 'symbol': symbol,
        'data_start': meta['start'], 'data_end': meta['end'],
        'train_start': split_info['train_start'], 'train_end': split_info['train_end'],
        'val_start': split_info['val_start'], 'val_end': split_info['val_end'],
        'test_start': split_info['test_start'], 'test_end': split_info['test_end'],
        'horizon': horizon, 'threshold': threshold,
        'feature_count': len(feature_cols), 'best_model': best_model_name or '',
        'status': 'completed',
        'config': {'use_regime': use_regime, 'train_ratio': train_ratio,
                   'val_ratio': val_ratio, 'feature_cols': feature_cols},
        'metrics': {n: r for n, r in model_results['models'].items() if r.get('status') == 'success'},
        'run_dir': str(run_dir),
    }
    save_training_run(run_data)

    # Cache for API access
    _cache[symbol] = {
        'run_id': run_id, 'model': best_model if best_model_name else None,
        'model_name': best_model_name, 'feature_cols': feature_cols,
        'df': df, 'train_df': train_df, 'val_df': val_df, 'test_df': test_df,
        'split_info': split_info, 'target_info': target_info,
        'quality': quality, 'meta': meta, 'regime_dist': regime_dist,
        'model_results': model_results, 'backtest': bt_result,
        'bt_metrics': bt_metrics, 'global_importance': global_imp,
        'clusterer': clusterer if clusterer.fitted else None,
    }

    logger.info(f'=== Training Pipeline Complete: best={best_model_name} ===')
    return {
        'run_id': run_id, 'symbol': symbol, 'status': 'completed',
        'dataset_info': {'source': meta['source'], 'symbol': symbol,
            'start': meta['start'], 'end': meta['end'], 'rows': meta['rows'],
            'quality': quality.to_dict()},
        'split_info': split_info,
        'class_distribution': target_info['class_distribution'],
        'regime_distribution': regime_dist,
        'model_results': {n: {
            'name': n, 'status': r.get('status',''),
            'train_time': r.get('train_time', 0),
            'val_metrics': r.get('val_metrics', {}),
            'test_metrics': r.get('test_metrics', {}),
        } for n, r in model_results['models'].items()},
        'best_model': best_model_name or '',
        'feature_count': len(feature_cols),
        'backtest_metrics': bt_metrics,
        'timestamp': datetime.now().isoformat(),
    }

def get_cache(symbol):
    return _cache.get(symbol)

def load_cached_model(symbol):
    from app.storage.database import get_latest_run
    if symbol in _cache: return _cache[symbol]
    run = get_latest_run(symbol)
    if not run: return None
    run_dir = Path(run['run_dir'])
    if not run_dir.exists(): return None
    best = run['best_model']
    mp = run_dir / f'{best}.joblib'
    if not mp.exists(): return None
    model = joblib.load(mp)
    fc_path = run_dir / 'feature_cols.joblib'
    feature_cols = joblib.load(fc_path) if fc_path.exists() else []
    imp_path = run_dir / 'feature_importance.json'
    global_imp = json.loads(imp_path.read_text()) if imp_path.exists() else []
    # Load data for context
    try:
        df, meta, quality = load_data(symbol)
        df, built_cols = build_features(df)
        df = detect_regimes_rule_based(df)
        df = get_regime_features(df)
        target_df, target_info = generate_target(df, horizon=run['horizon'], threshold=run['threshold'])
        config_json = json.loads(run.get('config_json', '{}'))
        tr = config_json.get('train_ratio', 0.7)
        vr = config_json.get('val_ratio', 0.15)
        test_r = 1.0 - tr - vr
        train_df, val_df, test_df, split_info = chronological_split(
            target_df, train_ratio=tr, val_ratio=vr, test_ratio=test_r)
    except:
        return None
    metrics_json = json.loads(run.get('metrics_json', '{}'))
    _cache[symbol] = {
        'run_id': run['id'], 'model': model,
        'model_name': best, 'feature_cols': feature_cols,
        'df': target_df, 'train_df': train_df, 'val_df': val_df, 'test_df': test_df,
        'split_info': split_info, 'target_info': target_info,
        'quality': quality, 'meta': meta,
        'regime_dist': target_df['regime_label'].value_counts().to_dict() if 'regime_label' in target_df.columns else {},
        'model_results': {'models': metrics_json}, 'backtest': {},
        'bt_metrics': {}, 'global_importance': global_imp,
        'clusterer': None,
    }
    return _cache[symbol]
""")

print('Pipeline orchestrator done')
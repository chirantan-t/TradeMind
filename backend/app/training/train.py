import logging
import argparse
import uuid
import joblib
import pandas as pd
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.data.loader import load_data
from app.data.provider import get_universe
from app.features.builder import build_features
from app.features.target import generate_target
from app.data.splitter import chronological_split
from app.regimes.detector import detect_regimes_rule_based, get_regime_features
from app.regimes.clustering import RegimeClusterer
from app.models.trainer import train_all_models
from app.explainability.shap_explainer import get_global_shap_importance
from app.explainability.feature_importance import get_model_feature_importance
from app.storage.database import save_training_run

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def train_global_model(universe_size: int = None, horizon: int = 5, threshold: float = 0.01):
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_global_' + str(uuid.uuid4())[:4]
    logger.info(f"=== Starting Global Model Training: run={run_id} ===")
    
    stocks = get_universe()
    if universe_size:
        stocks = stocks[:universe_size]
    
    # Extract Benchmark (NIFTY 50) first
    bench_symbol = '^NSEI'
    bench_df, _, _ = load_data(bench_symbol)
    
    all_dfs = []
    feature_cols = []
    
    # 1. Process all stocks and pool the data
    for stock in stocks:
        symbol = stock['symbol']
        if symbol == bench_symbol:
            continue
            
        logger.info(f"Processing {symbol}...")
        try:
            df, _, _ = load_data(symbol)
            df, f_cols = build_features(df, benchmark_df=bench_df)
            feature_cols = f_cols  # assumes consistent columns
            df = detect_regimes_rule_based(df)
            df = get_regime_features(df)
            regime_feats = ['regime_bull', 'regime_bear', 'regime_sideways']
            feature_cols = list(set(feature_cols + regime_feats))
            
            df, target_info = generate_target(df, horizon=horizon, threshold=threshold)
            df['symbol'] = symbol
            all_dfs.append(df)
        except Exception as e:
            logger.error(f"Failed processing {symbol}: {e}")
            
    if not all_dfs:
        logger.error("No data processed!")
        return
        
    global_df = pd.concat(all_dfs, ignore_index=True)
    global_df = global_df.sort_values('Date').reset_index(drop=True)
    logger.info(f"Pooled dataset: {len(global_df)} total observations across {len(all_dfs)} stocks.")
    
    # 2. Chronological Split (over the entire pooled set)
    train_df, val_df, test_df, split_info = chronological_split(
        global_df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15
    )
    
    # 3. Train Regime Clusterer globally (optional, on training data)
    clusterer = RegimeClusterer(n_clusters=3)
    try:
        clusterer.fit(train_df)
        run_dir = settings.artifacts_path / 'models' / 'global' / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        clusterer.save(str(run_dir / 'regime_clusterer.joblib'))
    except Exception as e:
        logger.warning(f"Global Regime clustering failed: {e}")
        run_dir = settings.artifacts_path / 'models' / 'global' / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
    # 4. Train Models
    logger.info("Training models on global dataset...")
    # NOTE: train_all_models expects run_dir setup, let's adapt it to use run_dir directly or we mock it.
    model_results = train_all_models(
        train_df, val_df, test_df, feature_cols,
        run_id=run_id, symbol="GLOBAL"
    )
    
    best_model_name = model_results['best_model']
    actual_run_dir = Path(model_results['run_dir'])
    
    if best_model_name:
        best_model = joblib.load(actual_run_dir / f'{best_model_name}.joblib')
        X_test = test_df[feature_cols].values
        
        # Save feature importance
        global_imp = get_global_shap_importance(best_model, X_test, feature_cols)
        if global_imp is None:
            global_imp = get_model_feature_importance(best_model, feature_cols)
            
        if global_imp:
            import json
            with open(actual_run_dir / 'feature_importance.json', 'w') as f:
                json.dump(global_imp[:20], f, indent=2)
                
        # Also copy the best model into a "latest" global pointer directory
        latest_dir = settings.artifacts_path / 'models' / 'global' / 'latest'
        latest_dir.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(best_model, latest_dir / 'model.joblib')
        joblib.dump(feature_cols, latest_dir / 'feature_cols.joblib')
        if global_imp:
            with open(latest_dir / 'feature_importance.json', 'w') as f:
                json.dump(global_imp[:20], f, indent=2)
                
    run_data = {
        'run_id': run_id, 'symbol': 'GLOBAL',
        'data_start': global_df['Date'].min().strftime('%Y-%m-%d'), 
        'data_end': global_df['Date'].max().strftime('%Y-%m-%d'),
        'train_start': split_info['train_start'], 'train_end': split_info['train_end'],
        'val_start': split_info['val_start'], 'val_end': split_info['val_end'],
        'test_start': split_info['test_start'], 'test_end': split_info['test_end'],
        'horizon': horizon, 'threshold': threshold,
        'feature_count': len(feature_cols), 'best_model': best_model_name or '',
        'status': 'completed',
        'config': {'use_regime': True, 'train_ratio': 0.7, 'val_ratio': 0.15, 'feature_cols': feature_cols},
        'metrics': {n: r for n, r in model_results['models'].items() if r.get('status') == 'success'},
        'run_dir': str(actual_run_dir),
    }
    save_training_run(run_data)
    logger.info(f"=== Global Model Training Complete: best={best_model_name} ===")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='Limit number of stocks to process')
    args = parser.parse_args()
    
    train_global_model(universe_size=args.limit)

import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/models/trainer.py', """import logging, time, json, uuid
from pathlib import Path
from datetime import datetime
import numpy as np, pandas as pd, joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from app.models.evaluator import evaluate_model
from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_CONFIGS = {
    'LogisticRegression': lambda: Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, class_weight='balanced',
            random_state=42, C=1.0, multi_class='multinomial', solver='lbfgs'))]),
    'RandomForest': lambda: Pipeline([
        ('clf', RandomForestClassifier(n_estimators=200, max_depth=10,
            min_samples_split=10, class_weight='balanced', random_state=42, n_jobs=-1))]),
    'GradientBoosting': lambda: Pipeline([
        ('clf', GradientBoostingClassifier(n_estimators=200, max_depth=5,
            learning_rate=0.1, min_samples_split=10, random_state=42, subsample=0.8))]),
    'SVM': lambda: Pipeline([
        ('scaler', StandardScaler()),
        ('clf', SVC(kernel='rbf', probability=True, class_weight='balanced',
            random_state=42, C=1.0, gamma='scale'))]),
}

def train_all_models(train_df, val_df, test_df, feature_cols, target_col='target',
                     run_id=None, symbol=''):
    if run_id is None: run_id = str(uuid.uuid4())[:8]
    run_dir = settings.artifacts_path / 'runs' / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    X_tr = train_df[feature_cols].values
    y_tr = train_df[target_col].values
    X_val = val_df[feature_cols].values
    y_val = val_df[target_col].values
    X_te = test_df[feature_cols].values
    y_te = test_df[target_col].values

    results = {}
    best_name = None
    best_f1 = -1
    labels = ['BUY', 'HOLD', 'SELL']

    for name, make_pipe in MODEL_CONFIGS.items():
        logger.info(f'Training {name}...')
        t0 = time.time()
        try:
            pipe = make_pipe()
            pipe.fit(X_tr, y_tr)
            tt = time.time() - t0
            vm = evaluate_model(pipe, X_val, y_val, labels)
            tm = evaluate_model(pipe, X_te, y_te, labels)
            mp = run_dir / f'{name}.joblib'
            joblib.dump(pipe, mp)
            r = {'name': name, 'train_time': round(tt, 2),
                 'val_metrics': vm, 'test_metrics': tm,
                 'model_path': str(mp), 'status': 'success'}
            if vm['f1_weighted'] > best_f1:
                best_f1 = vm['f1_weighted']; best_name = name
            logger.info(f'{name}: val_f1={vm["f1_weighted"]:.4f} test_f1={tm["f1_weighted"]:.4f} time={tt:.1f}s')
        except Exception as e:
            logger.error(f'Failed {name}: {e}')
            r = {'name': name, 'status': 'failed', 'error': str(e)}
        results[name] = r

    joblib.dump(feature_cols, run_dir / 'feature_cols.joblib')
    cfg = {'run_id': run_id, 'symbol': symbol, 'timestamp': datetime.now().isoformat(),
           'feature_count': len(feature_cols), 'train_samples': len(train_df),
           'val_samples': len(val_df), 'test_samples': len(test_df),
           'best_model': best_name, 'models': list(results.keys())}
    with open(run_dir / 'config.json', 'w') as f: json.dump(cfg, f, indent=2)
    met = {}
    for n, r in results.items():
        if r['status'] == 'success':
            met[n] = {'val': r['val_metrics'], 'test': r['test_metrics'], 'train_time': r['train_time']}
    with open(run_dir / 'metrics.json', 'w') as f: json.dump(met, f, indent=2, default=str)
    return {'run_id': run_id, 'run_dir': str(run_dir), 'models': results,
            'best_model': best_name, 'best_val_f1': best_f1}
""")
print('trainer done')
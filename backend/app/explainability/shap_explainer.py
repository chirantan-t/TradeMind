import logging, numpy as np
logger = logging.getLogger(__name__)
_shap_ok = True
try:
    import shap
except ImportError:
    _shap_ok = False

def explain_prediction_shap(model, X_single, feature_names, predicted_class=None):
    if not _shap_ok: return None
    try:
        clf = model.named_steps.get('clf', model)
        Xi = X_single.reshape(1, -1)
        if 'scaler' in model.named_steps:
            Xi = model.named_steps['scaler'].transform(Xi)
        if hasattr(clf, 'estimators_') or hasattr(clf, 'tree_'):
            ex = shap.TreeExplainer(clf)
            sv = ex.shap_values(Xi)
        else:
            return None
        if isinstance(sv, list):
            vals = sv[predicted_class][0] if predicted_class is not None and predicted_class < len(sv) else sv[0][0]
        elif len(sv.shape) == 3:
            vals = sv[predicted_class][0] if predicted_class is not None and predicted_class < sv.shape[0] else sv[0][0]
        else:
            vals = sv[0]
        res = [{'feature': f, 'contribution': float(v)} for f, v in zip(feature_names, vals)]
        res.sort(key=lambda x: abs(x['contribution']), reverse=True)
        return res
    except Exception as e:
        logger.warning(f'SHAP failed: {e}')
        return None

def get_global_shap_importance(model, X, feature_names, max_samples=200):
    if not _shap_ok: return None
    try:
        clf = model.named_steps.get('clf', model)
        Xi = X[:max_samples].copy()
        if 'scaler' in model.named_steps:
            Xi = model.named_steps['scaler'].transform(Xi)
        if hasattr(clf, 'estimators_') or hasattr(clf, 'tree_'):
            ex = shap.TreeExplainer(clf)
            sv = ex.shap_values(Xi)
            if isinstance(sv, list):
                ma = np.mean([np.abs(s).mean(axis=0) for s in sv], axis=0)
            elif len(sv.shape) == 3:
                ma = np.abs(sv).mean(axis=(0, 1))
            else:
                ma = np.abs(sv).mean(axis=0)
            res = [{'feature': f, 'importance': float(v)} for f, v in zip(feature_names, ma)]
            res.sort(key=lambda x: x['importance'], reverse=True)
            return res
        return None
    except Exception as e:
        logger.warning(f'Global SHAP failed: {e}')
        return None

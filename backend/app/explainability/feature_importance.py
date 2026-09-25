import logging, numpy as np
logger = logging.getLogger(__name__)

def get_model_feature_importance(model, feature_names):
    clf = model.named_steps.get('clf', model)
    if hasattr(clf, 'feature_importances_'):
        imp = clf.feature_importances_
        r = [{'feature': f, 'importance': float(v)} for f, v in zip(feature_names, imp)]
        r.sort(key=lambda x: x['importance'], reverse=True)
        return r
    if hasattr(clf, 'coef_'):
        coef = np.abs(clf.coef_).mean(axis=0)
        if 'scaler' in model.named_steps:
            coef = coef * model.named_steps['scaler'].scale_
        r = [{'feature': f, 'importance': float(v)} for f, v in zip(feature_names, coef)]
        r.sort(key=lambda x: x['importance'], reverse=True)
        return r
    return None

def get_prediction_contributions(model, X_single, feature_names, predicted_class=None):
    clf = model.named_steps.get('clf', model)
    if hasattr(clf, 'coef_'):
        Xt = X_single.reshape(1, -1)
        if 'scaler' in model.named_steps:
            Xt = model.named_steps['scaler'].transform(Xt)
        coef = clf.coef_[predicted_class] if predicted_class is not None and predicted_class < clf.coef_.shape[0] else clf.coef_[0]
        contribs = coef * Xt[0]
        r = [{'feature': f, 'contribution': float(v)} for f, v in zip(feature_names, contribs)]
        r.sort(key=lambda x: abs(x['contribution']), reverse=True)
        return r
    imp = get_model_feature_importance(model, feature_names)
    if imp:
        for item in imp:
            idx = feature_names.index(item['feature']) if item['feature'] in feature_names else 0
            item['contribution'] = item['importance'] * (1 if X_single[idx] > 0 else -1)
        imp.sort(key=lambda x: abs(x['contribution']), reverse=True)
        return imp
    return []

_HNAMES = {
    'rsi_14': 'RSI(14)', 'macd': 'MACD', 'macd_histogram': 'MACD histogram',
    'volatility_20d': 'realized volatility', 'daily_return': 'daily return',
    'return_5d': '5-day return', 'return_14d': '14-day return',
    'momentum_14': '14-day momentum', 'momentum_20': '20-day momentum',
    'volume_zscore': 'volume z-score', 'atr_pct': 'ATR%',
    'trend_slope_20': 'trend slope', 'relative_strength': 'relative strength',
    'price_sma_50_ratio': 'price/SMA-50', 'rolling_drawdown_20': 'rolling drawdown',
    'regime_bull': 'bull regime', 'regime_bear': 'bear regime',
}

def _humanize(name):
    return _HNAMES.get(name, name.replace('_', ' '))

def generate_explanation_text(signal, confidence, regime, top_drivers, n=4):
    if not top_drivers:
        return f'{signal} signal with {confidence:.0%} model confidence in {regime} regime.'
    drivers = top_drivers[:n]
    sup = [d for d in drivers if d.get('contribution', 0) > 0]
    opp = [d for d in drivers if d.get('contribution', 0) < 0]
    parts = []
    if sup:
        names = ', '.join(_humanize(d['feature']) for d in sup[:3])
        parts.append(f'{names} {"support" if len(sup)>1 else "supports"} the {signal} classification')
    if opp:
        names = ', '.join(_humanize(d['feature']) for d in opp[:2])
        parts.append(f'{names} {"reduce" if len(opp)>1 else "reduces"} model confidence')
    return (', while '.join(parts) + '.') if parts else f'{signal} signal detected.'

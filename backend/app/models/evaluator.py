import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix)

def evaluate_model(model, X, y, label_names=None):
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X) if hasattr(model, 'predict_proba') else None
    m = {
        'accuracy': float(accuracy_score(y, y_pred)),
        'precision_weighted': float(precision_score(y, y_pred, average='weighted', zero_division=0)),
        'recall_weighted': float(recall_score(y, y_pred, average='weighted', zero_division=0)),
        'f1_weighted': float(f1_score(y, y_pred, average='weighted', zero_division=0)),
        'f1_macro': float(f1_score(y, y_pred, average='macro', zero_division=0)),
    }
    if y_proba is not None:
        try:
            if len(np.unique(y)) > 1:
                m['roc_auc'] = float(roc_auc_score(y, y_proba, multi_class='ovr', average='weighted'))
            else: m['roc_auc'] = None
        except: m['roc_auc'] = None
    else: m['roc_auc'] = None
    cm = confusion_matrix(y, y_pred)
    m['confusion_matrix'] = cm.tolist()
    if label_names is None:
        label_names = [str(i) for i in sorted(np.unique(np.concatenate([y, y_pred])))]
    per_class = {}
    classes = sorted(np.unique(np.concatenate([y, y_pred])))
    for i, cls in enumerate(classes):
        name = label_names[i] if i < len(label_names) else str(cls)
        mt = y == cls; mp = y_pred == cls
        tp = int(np.sum(mt & mp)); fp = int(np.sum(~mt & mp)); fn = int(np.sum(mt & ~mp))
        p = tp/(tp+fp) if (tp+fp)>0 else 0; r = tp/(tp+fn) if (tp+fn)>0 else 0
        f = 2*p*r/(p+r) if (p+r)>0 else 0
        per_class[name] = {'precision': round(p,4), 'recall': round(r,4), 'f1': round(f,4)}
    m['per_class'] = per_class
    return m

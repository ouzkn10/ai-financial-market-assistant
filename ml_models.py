import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


def fit_light_model(X, y):
    
    models = []

    # Logistic Regression
    try:
        lr = LogisticRegression(
            max_iter=200,
            n_jobs=None,
            solver="lbfgs"
        )
        lr.fit(X, y)
        models.append(lr)
    except Exception:
        pass

    # RandomForest
    try:
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=5,
            random_state=42
        )
        rf.fit(X, y)
        models.append(rf)
    except Exception:
        pass

    return models


def ensemble_predict_proba(models, X):
   
    if not models:
        return np.tile([0.5, 0.5], (X.shape[0], 1))

    probs = []
    for m in models:
        try:
            p = m.predict_proba(X)
            if p.shape[1] == 1:
                p = np.hstack([1 - p, p])
            probs.append(p)
        except Exception:
            pass

    if not probs:
        return np.tile([0.5, 0.5], (X.shape[0], 1))

    P = np.mean(probs, axis=0)
    return P

"""
    Trains the ClaimFlow risk-prediction model on the syntehtic dataset produced
    by data_generator
    
    Produces:
        models/model.pkl   ------------------------> Trained XGBoost classifier (joblib)
        models/model_metadata.json ----------------> version, feature list, thresholds, metrics

    This model estimates and "investigation probability" for a claim. It is 
    explicitly NOT a fraud determination.
"""


# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import json, os ,sys, joblib
import numpy as np 
import pandas as pd 
from sklearn.metrics import average_precision_score , classification_report , roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0 , os.path.join(os.path.dirname(__file__) , ".."))
from app.ml.features import FEATURE_COLUMNS, TARGET_COLUMN, build_training_frame

DATA_DIR = os.getenv("DATA_DIR" , os.path.join(os.path.dirname(__file__) , ".." , "data"))
MODEL_DIR = os.getenv("MODEL_DIR" , os.path.join(os.path.dirname(__file__) , ".." , "models"))
MODEL_VERSION = os.getenv("MODEL_VERSION" , "claim-risk-v1")
RANDOM_STATE = 42

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       model Creation Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def load_data() -> pd.DataFrame:
    claims = pd.read_csv(os.path.join(DATA_DIR, "claims.csv"))
    vehicles = pd.read_csv(os.path.join(DATA_DIR, "vehicles.csv"))
    return build_training_frame(claims, vehicles)


def train_xgboost(X_train, y_train):
    try:
        from xgboost import XGBClassifier
    except ImportError:
        print("xgboost not available, falling back to sklearn GradientBoostingClassifier")
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(random_state=RANDOM_STATE)
        model.fit(X_train, y_train)
        return model, "gradient_boosting"

    # scale_pos_weight compensates for the class imbalance (investigation
    # cases are a minority, matching realistic claim volumes).
    pos = y_train.sum()
    neg = len(y_train) - pos
    scale_pos_weight = float(neg / max(pos, 1))

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=3,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model, "xgboost"


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading + building training frame...")
    frame = load_data()
    print(f"Training frame shape: {frame.shape}")
    print(f"Positive rate: {frame[TARGET_COLUMN].mean():.4f}")

    X = frame[FEATURE_COLUMNS]
    y = frame[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    print("Training model...")
    model, algo = train_xgboost(X_train, y_train)

    print("Evaluating on held-out test set...")
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    roc_auc = roc_auc_score(y_test, probs)
    pr_auc = average_precision_score(y_test, probs)
    report = classification_report(y_test, preds, output_dict=True)

    print(f"ROC AUC: {roc_auc:.4f}")
    print(f"PR AUC:  {pr_auc:.4f}")
    print(classification_report(y_test, preds))

    if hasattr(model, "feature_importances_"):
        importances = dict(zip(FEATURE_COLUMNS, [float(v) for v in model.feature_importances_]))
        importances = dict(sorted(importances.items(), key=lambda kv: -kv[1]))
        print("\nFeature importances:")
        for k, v in importances.items():
            print(f"  {k:45s} {v:.4f}")
    else:
        importances = {}

    model_path = os.path.join(MODEL_DIR, "model.pkl")
    joblib.dump(model, model_path)

    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": algo,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "risk_level_thresholds": {"low_upper": 0.40, "high_lower": 0.70},
        "training_rows": int(len(frame)),
        "positive_rate": float(y.mean()),
        "metrics": {
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "classification_report": report,
        },
        "feature_importances": importances,
        "random_state": RANDOM_STATE,
        "note": (
            "Synthetic training data. investigation_label indicates a "
            "historical pattern match for investigation-worthy claims, "
            "not a fraud determination. Final decisions are made by human "
            "investigators."
        ),
    }
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model to {model_path}")
    print(f"Saved metadata to {os.path.join(MODEL_DIR, 'model_metadata.json')}")


if __name__ == "__main__":
    main()




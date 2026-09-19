"""
    Standalone evluation of an already-trained model against the current
    dataset. Useful after regenerating data with a different seed/volume or
    to sanity check a model before deploy it.

    OPENBOOK EXAM : Getting prediction for the whole data not like 80% train then show rest 20%

"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import json
import os
import sys

import joblib
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.ml.features import FEATURE_COLUMNS, TARGET_COLUMN, build_training_frame  # noqa: E402

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "models"))

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Evluation Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def main():
    model_path = os.path.join(MODEL_DIR, "model.pkl")
    if not os.path.exists(model_path):
        print(f"No model found at {model_path}. Run training/train_model.py first.")
        sys.exit(1)

    model = joblib.load(model_path)

    claims = pd.read_csv(os.path.join(DATA_DIR, "claims.csv"))
    vehicles = pd.read_csv(os.path.join(DATA_DIR, "vehicles.csv"))
    frame = build_training_frame(claims, vehicles)

    X = frame[FEATURE_COLUMNS]
    y = frame[TARGET_COLUMN]

    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)

    print(f"Rows evaluated: {len(frame)}")
    print(f"ROC AUC: {roc_auc_score(y, probs):.4f}")
    print(f"PR AUC:  {average_precision_score(y, probs):.4f}")
    print("\nConfusion matrix (rows=actual, cols=predicted):")
    print(confusion_matrix(y, preds))
    print("\nClassification report:")
    print(classification_report(y, preds))

    with open(os.path.join(MODEL_DIR, "model_metadata.json")) as f:
        meta = json.load(f)
    print(f"\nModel version: {meta.get('model_version')} ({meta.get('algorithm')})")
    print(f"Trained on {meta.get('training_rows')} rows, positive rate {meta.get('positive_rate'):.4f}")


if __name__ == "__main__":
    main()

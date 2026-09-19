"""
    Loads the train model once at process start and expose a simple
    predict(payload) function used by FASTAPI route
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os, json 
from typing import Any,Dict 
import joblib

from app.ml.features import build_feature_row_from_payload , risk_level_from_probability

MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "models"))
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")

_model = None
_metadata: Dict[str, Any] = {}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Prediction Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

class ModelNotLoadedError(RuntimeError):
    pass


def load_model():
    global _model, _metadata
    if not os.path.exists(MODEL_PATH):
        raise ModelNotLoadedError(
            f"No trained model found at {MODEL_PATH}. Run training/train_model.py first."
        )
    _model = joblib.load(MODEL_PATH)
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH) as f:
            _metadata = json.load(f)
    else:
        _metadata = {"model_version": "unknown"}
    return _model


def is_loaded() -> bool:
    return _model is not None


def get_metadata() -> Dict[str, Any]:
    return _metadata


def predict(payload: Dict[str, Any]) -> Dict[str, Any]:
    if _model is None:
        raise ModelNotLoadedError("Model is not loaded. Call load_model() at startup.")

    row = build_feature_row_from_payload(payload)
    probability = float(_model.predict_proba(row)[:, 1][0])
    thresholds = _metadata.get("risk_level_thresholds", {"low_upper": 0.40, "high_lower": 0.70})
    level = risk_level_from_probability(
        probability, (thresholds["low_upper"], thresholds["high_lower"])
    )

    return {
        "risk_probability": round(probability, 4),
        "risk_level": level,
        "model_version": _metadata.get("model_version", "unknown"),
    }

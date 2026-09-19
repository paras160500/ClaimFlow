# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import logging

from fastapi import APIRouter, HTTPException

from app.ml import predict as predict_module
from app.schemas.claim import ClaimFeaturesInput, RiskPredictionResponse

logger = logging.getLogger("claimflow.prediction")

router = APIRouter(tags=["prediction"])

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       class Schema Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

@router.post("/predict", response_model=RiskPredictionResponse)
def predict_claim_risk(payload: ClaimFeaturesInput):
    """
    Stage-1 endpoint: pure ML risk/investigation-probability prediction.

    Rules-engine, relationship-analysis, Pinecone retrieval and LLM
    explanation are added in Stage 2 behind /analyze-claim, which will call
    this same model internally.
    """
    if not predict_module.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Risk model is not loaded on this instance. Train and deploy model.pkl first.",
        )

    try:
        result = predict_module.predict(payload.model_dump())
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction failed for claim_id=%s", payload.claim_id)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    return RiskPredictionResponse(claim_id=payload.claim_id, **result)

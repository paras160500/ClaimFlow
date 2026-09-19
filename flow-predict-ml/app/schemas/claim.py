"""
    Request/response schemas for the stage-1 prediction end point.

    Stage 1 only exposes ML risks prediction. The full analyze-claim endpoint
    (ML + rules + relationships + Pinecone + LLM ) is built in another stage
    once AI layer as RAG+LLM exists.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

from typing import Optional
from pydantic import BaseModel, Field

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       class Schema Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

class ClaimFeaturesInput(BaseModel):
    """
    Raw feature inputs for a single claim. In later stages, Node will fetch
    these values from Supabase and pass them straight through; for Stage 1
    they can also be supplied directly (e.g. from a CSV row) for testing.
    """

    claim_id: Optional[str] = Field(None, description="Optional, echoed back in the response")

    claim_amount: float = Field(..., ge=0)
    policy_age_days: float = Field(..., description="Days between policy start and claim date")
    vehicle_age: Optional[float] = Field(None, ge=0)
    previous_claim_count: Optional[float] = Field(0, ge=0)
    days_since_previous_claim: Optional[float] = Field(
        -1, description="-1 if there is no previous claim"
    )
    customer_claim_frequency: Optional[float] = Field(0, ge=0)
    repair_shop_claim_count_prior: Optional[float] = Field(0, ge=0)
    repair_shop_investigation_rate_prior: Optional[float] = Field(0, ge=0, le=1)

    # Used to derive ratio features; optional but recommended for accuracy.
    vehicle_value: Optional[float] = Field(None, gt=0)
    customer_avg_claim_amount_prior: Optional[float] = Field(None, gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "claim_id": "CL050001",
                "claim_amount": 133300,
                "policy_age_days": 18,
                "vehicle_age": 4,
                "previous_claim_count": 4,
                "days_since_previous_claim": 4,
                "customer_claim_frequency": 6,
                "repair_shop_claim_count_prior": 100,
                "repair_shop_investigation_rate_prior": 0.135,
                "vehicle_value": 393000,
                "customer_avg_claim_amount_prior": 207033.33,
            }
        }


class RiskPredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    claim_id: Optional[str] = None
    risk_probability: float
    risk_level: str
    model_version: str
    disclaimer: str = (
        "This is a model-generated risk/investigation-probability estimate, "
        "not a determination of fraud. The final decision belongs to a "
        "human investigator."
    )

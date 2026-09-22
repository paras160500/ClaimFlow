# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import logging 
from fastapi import APIRouter, HTTPException

from app.llm.investigator import analyze_claim
from app.schemas.investigation import AnalyzeClaimRequest , AnalyzeClaimResponse

logger = logging.getLogger("claimflow.investigation")
router = APIRouter(tags=["investigation"])

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Document Processing statement
# ════════════════════════════════════════════════════════════════════════════════════════════════

@router.post("/analyze-claim" , response_model=AnalyzeClaimResponse)
def analyze_claim_endpoint(payload : AnalyzeClaimRequest):
    """
        Stage-2 endpoint : full investigation bundle for one claim -- ML Risk,
        rules check ,relationship analysis , retrieved policy/ investigator-note
        evidence and LLM investigation summary

        This is the endpoint the Node backend will call from
        POST /api/claims/:claimId/analyze 
    """

    result = analyze_claim(payload.claim_id)
    if result.get("error") == "not_found":
        raise HTTPException(status = 404 , detail=result['message'])
    return AnalyzeClaimResponse(**result)

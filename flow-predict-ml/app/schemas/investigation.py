# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           Schema statement
# ════════════════════════════════════════════════════════════════════════════════════════════════

class AnalyzeClaimRequest(BaseModel):
    claim_id : str 

    class Config:
        json_schema_extra = {"example" : {"claim_id" : "CL050001"}}


class AnalyzeClaimResponse(BaseModel):
    claim_id: str
    risk_probability: Optional[float] = None
    risk_level: Optional[str] = None
    model_version: Optional[str] = None
    rule_results: List[Dict[str, Any]] = []
    relationships: Dict[str, Any] = {}
    retrieved_policy_evidence: List[Dict[str, Any]] = []
    retrieved_investigator_notes: List[Dict[str, Any]] = []
    summary: str
    summary_source: str
    disclaimer: str

    model_config = {"protected_namespaces": ()}
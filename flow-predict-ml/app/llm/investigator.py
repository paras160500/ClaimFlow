"""
    Orcastrates a full claim investigation: this is what POST /api/analyze-claim
    calls. Each step is independently error-handled so a failure in one component
    degrade fracefully instead of crashing whole response.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import logging 
from typing import Any,Dict 

from app.db import fetch_claim_bundle
from app.llm.client import generate_investigation_summary
from app.llm.prompts import SYSTEM_PROMPT , build_prompt
from app.ml import predict as predict_module 
from app.ml.features import build_feature_row_from_payload
from app.rag.retriever import get_retriever
from app.relationships.analyzer import analyze as analyze_relationships
from app.rules.engine import run_all_rules

logger = logging.getLogger("claimflow.llm.investigator")

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Document Processing statement
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _run_ml(claim : Dict[str , Any]) -> Dict[str , Any]:
    if not predict_module.is_loaded():
        return {
            "risk_probability" : 0.0 ,
            "risk_level" : "UNKNOWN",
            "model_version" : "unavailable",
            "error" : "Risk model is not loaded on this instance."
        }

    try:
        payload = {
            "claim_amount": claim["claim_amount"],
            "policy_age_days": claim["policy_age_days"],
            "vehicle_age": 2026 - claim["manufacture_year"],
            "previous_claim_count": claim["previous_claim_count"],
            "days_since_previous_claim": claim["days_since_previous_claim"],
            "customer_claim_frequency": claim["customer_claim_frequency"],
            "repair_shop_claim_count_prior": claim["repair_shop_claim_count_prior"],
            "repair_shop_investigation_rate_prior": claim["repair_shop_investigation_rate_prior"],
            "vehicle_value": claim["vehicle_value"],
            "customer_avg_claim_amount_prior": claim["customer_avg_claim_amount_prior"],
        }
        return predict_module.predict(payload)
    except Exception as exc:
        logger.exception("ML Prediction failed for claim %s" , claim.get("claim_id"))
        return {
            "risk_probability" : 0.0 , "risk_level" : "UNKNOWN" , "model_version" : "error" , "error" : str(exc)
        }


def _run_rag(claim : Dict[str , Any]):
    """
        Returns (policy_evidence , investigator_nodes); never raises.
    """
    try:
        retriever = get_retriever()
        policy_query = f"{claim['policy_type']} policy coverage exclusions required documents"
        policy_evidence = retriever.retrieve(
            policy_query, top_k=3,
            metadata_filter={"document_type": "policy", "policy_type": claim["policy_type"]},
        )
    except Exception as exc:  
        logger.error("Policy evidence retrieval failed for claim %s: %s", claim.get("claim_id"), exc)
        policy_evidence = []

    try:
        notes_query = f"investigation history for repair shop {claim.get('repair_shop_id', '')} similar claims"
        investigator_notes = retriever.retrieve(
            notes_query, top_k=3, metadata_filter={"document_type": "investigator_note"}
        )
    except Exception as exc:  
        logger.error("Investigator note retrieval failed for claim %s: %s", claim.get("claim_id"), exc)
        investigator_notes = []

    return policy_evidence, investigator_notes



def analyze_claim(claim_id: str) -> Dict[str, Any]:
    claim = fetch_claim_bundle(claim_id)
    if claim is None:
        return {"error": "not_found", "message": f"No claim found with id {claim_id}"}

    ml_result = _run_ml(claim)
    rule_results = run_all_rules(claim)
    relationships = analyze_relationships(claim)
    policy_evidence, investigator_notes = _run_rag(claim)

    prompt = build_prompt(claim, ml_result, rule_results, relationships, policy_evidence, investigator_notes)
    llm_result = generate_investigation_summary(
        SYSTEM_PROMPT, prompt, claim, ml_result, rule_results, relationships
    )

    return {
        "claim_id": claim_id,
        "risk_probability": ml_result.get("risk_probability"),
        "risk_level": ml_result.get("risk_level"),
        "model_version": ml_result.get("model_version"),
        "rule_results": rule_results,
        "relationships": relationships,
        "retrieved_policy_evidence": policy_evidence,
        "retrieved_investigator_notes": investigator_notes,
        "summary": llm_result["summary"],
        "summary_source": llm_result["source"],
        "disclaimer": (
            "This is a model-generated risk/investigation-probability estimate and an "
            "AI-generated summary of retrieved evidence -- not a determination of fraud. "
            "The final decision belongs to a human investigator."
        ),
    }
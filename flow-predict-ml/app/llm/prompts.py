"""
    Prompt construction for the investigation-summary LLM call.
    The system prompt is deliberately strict about terminology because 
    the LLM's only job is to explain what the other components already
    computed -- it must not invent numbers , invent relationships
    or make the call itself.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

from typing import Any, Dict, List 

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                          Prompt statement
# ════════════════════════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an assistant to insurance claim investigators at an internal claim \
investigation platform called ClaimFlow. You write concise, factual investigation summaries \
from data that has already been computed by other systems (a risk model, a rules engine, a \
relationship-analysis query, and retrieved policy/investigator-note text).

Strict rules:
- Never state or imply that a person committed fraud. Use terms like "risk score", \
"investigation probability", "anomaly", "risk signal", or "warrants further review" instead.
- Never invent facts, numbers, relationships, or policy wording. Only use what is given to you \
in the CLAIM DATA section below.
- Do not make the final decision. The final decision (approve / request documents / investigate \
further / reject) belongs to the human investigator. You may suggest what to verify.
- Be concise: a short summary, a short list of key signals, a short policy-context note, and a \
short list of recommended verification steps. No more than ~180 words total.
- If a section of input data is empty, simply omit that part rather than guessing.
"""


USER_PROMPT_TEMPLATE = """CLAIM DATA

Claim: {claim_id}
Claim type: {claim_type}
Claim amount: {claim_amount}
Policy type/version: {policy_type} {policy_version}
Policy age at time of claim: {policy_age_days} days
Vehicle: {vehicle_make} {vehicle_model} ({vehicle_year})

ML RISK ASSESSMENT
Risk probability: {risk_probability}
Risk level: {risk_level}

RULES ENGINE RESULTS
{rules_text}

RELATIONSHIP ANALYSIS
- Previous claims at this repair shop: {shop_total_claims} (previously investigated: {shop_investigated_claims})
- Previous claims for this vehicle: {vehicle_total_claims}
- Previous claims for this customer: {customer_total_claims}

RETRIEVED POLICY EVIDENCE
{policy_evidence_text}

RETRIEVED INVESTIGATOR NOTES
{investigator_notes_text}

Write the investigation summary now, following the system instructions exactly."""


def _format_rules(rule_results : List[Dict[str,Any]]) -> str:
    if not rule_results:
        return "(no rule results available)"
    lines = []
    for r in rule_results:
        marker = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}.get(r["status"], r["status"])
        lines.append(f"- {r['rule']}: {marker} - {r['message']}")
    return "\n".join(lines)


def _format_evidence(evidence : List[Dict[str,Any]]) -> str:
    if not evidence:
        return "(no policy evidence retrieved)"
    return "\n".join(f'- "{e["text"][:220].strip()}"' for e in evidence)


def _format_notes(notes: List[Dict[str, Any]]) -> str:
    if not notes:
        return "(no related investigator notes retrieved)"
    return "\n".join(f'- {n["text"][:220].strip().replace(chr(10), " ")}' for n in notes)


def build_prompt(
    claim: Dict[str, Any],
    ml_result: Dict[str, Any],
    rule_results: List[Dict[str, Any]],
    relationships: Dict[str, Any],
    policy_evidence: List[Dict[str, Any]],
    investigator_notes: List[Dict[str, Any]],
) -> str:
    return USER_PROMPT_TEMPLATE.format(
        claim_id=claim["claim_id"],
        claim_type=claim["claim_type"],
        claim_amount=f"{claim['claim_amount']:,.0f}",
        policy_type=claim["policy_type"],
        policy_version=claim["policy_version_id"],
        policy_age_days=f"{claim['policy_age_days']:.0f}",
        vehicle_make=claim["make"],
        vehicle_model=claim["model"],
        vehicle_year=claim["manufacture_year"],
        risk_probability=f"{ml_result['risk_probability']:.0%}",
        risk_level=ml_result["risk_level"],
        rules_text=_format_rules(rule_results),
        shop_total_claims=relationships["repair_shop"]["total_claims"],
        shop_investigated_claims=relationships["repair_shop"]["investigated_claims"],
        vehicle_total_claims=relationships["vehicle"]["total_claims"],
        customer_total_claims=relationships["customer"]["total_claims"],
        policy_evidence_text=_format_evidence(policy_evidence),
        investigator_notes_text=_format_notes(investigator_notes),
    )
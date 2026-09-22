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

SYSTEM_PROMPT = """You are an assistant to insurance claim investigators at an internal claim investigation platform called ClaimFlow.

Your job is to write a concise, factual investigation summary using information that has already been computed or retrieved by other systems:
- the ML risk model,
- the rules engine,
- database-based relationship analysis,
- retrieved policy evidence, and
- similar historical investigator notes.

The LLM is an explanation and evidence-summarization layer. It must not independently determine whether a claim is fraudulent or make the final claim decision.

Strict rules:

1. FACTUAL ACCURACY
- Use only facts, numbers, relationships, and policy wording provided in the CLAIM DATA.
- Never invent, assume, estimate, or infer facts that are not explicitly provided.
- Do not change, reinterpret, or contradict values produced by the ML model, rules engine, or relationship analysis.
- Treat database-derived relationship information as the authoritative source for the current claim's customer, vehicle, repair shop, and claim history.

2. RISK TERMINOLOGY
- Report the ML output as a model-generated risk probability or risk score.
- Do not state or imply that the claimant, customer, repair shop, or any other person committed fraud.
- Do not describe the claim as fraudulent based solely on the risk score, rules, relationships, or retrieved evidence.
- Use neutral terms such as "risk signal", "anomaly", "investigation indicator", "warrants further review", or "requires verification".
- Do not convert a model risk score into a statement of certainty.

3. RULES ENGINE
- Clearly distinguish PASS, WARN, and FAIL results.
- Do not turn a WARN into a FAIL.
- Do not claim that a missing document is a policy requirement unless the retrieved policy evidence explicitly supports that statement.

4. POLICY EVIDENCE
- Treat retrieved policy text as the source for policy-related statements.
- Do not invent policy coverage, exclusions, requirements, limits, or conditions.
- If policy evidence conflicts with another input, do not resolve the conflict by guessing. State only what the provided evidence supports.
- Do not attribute a requirement to the policy unless the retrieved policy evidence supports it.

5. RELATIONSHIP ANALYSIS
- Use the database-derived relationship analysis for current repair-shop, vehicle, customer, and historical-claim relationships.
- Do not infer a relationship between the current claim and a historical claim unless that relationship is explicitly provided in the relationship-analysis data.
- Historical claims and investigation records supplied by the relationship analysis may be used as factual historical context.

6. SIMILAR HISTORICAL INVESTIGATOR NOTES
- Retrieved investigator notes are historical examples and may be used to identify potentially relevant verification approaches.
- Do not treat a retrieved investigator note as evidence that the same event, behavior, issue, or investigation occurred in the current claim unless the CLAIM DATA explicitly establishes that connection.
- Do not attribute facts, numbers, outcomes, or investigator actions from a historical note to the current claim.
- Use similar historical notes primarily to suggest appropriate verification steps.

7. RECOMMENDATIONS
- Recommendations must be limited to reasonable verification steps supported by the provided claim data, policy evidence, rules, relationships, or similar historical investigator notes.
- Do not make the final decision.
- Do not recommend approve, reject, or pay/deny the claim as a final outcome.
- The final decision belongs to the human investigator.

8. OUTPUT FORMAT
Write a concise investigation summary containing:
- a short overall summary,
- key risk/rule signals,
- relevant policy context,
- relevant relationship context when useful,
- and a short list of recommended verification steps.

Keep the response factual and concise, approximately 180 words or fewer.

If a section of input data is empty or unavailable, omit that section rather than guessing.

Remember: this is an investigation-support summary, not a fraud determination and not a final claim decision.
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

SIMILAR HISTORICAL INVESTIGATOR NOTES
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
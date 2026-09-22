"""
    LLM CLient for the investigation-summary feature/

    If openai api key is set this calls openai chat completion. If its not
    set then it will not call openai api but it will generate template based summary directly 
    from the same structured data that would have gone into the prompt.
    This matches the projects error handing requirements.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import logging
import os 
from typing import Any, Dict, List 
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("claimflow.llm.client")
OPENAI_MODEL = os.getenv("OPENAI_MODEL" , "gpt-4o-mini")

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           Logic statement
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _call_openai(system_prompt : str , user_prompt : str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model = OPENAI_MODEL,
        messages = [
            {"role" : "system" , "content" : system_prompt},
            {"role" : "user" , "content" : user_prompt}
        ],
        temperature=0.2 ,
        max_tokens=350
    )
    return response.choices[0].message.content.strip()


def _fallback_summary(
    claim: Dict[str, Any],
    ml_result: Dict[str, Any],
    rule_results: List[Dict[str, Any]],
    relationships: Dict[str, Any],
) -> str:
    """Deterministic, non-LLM summary used when OpenAI is unavailable."""
    flagged_rules = [r for r in rule_results if r["status"] != "PASS"]
    signal_lines = [f"- {r['message']}" for r in flagged_rules] or ["- No rule-based signals were flagged."]

    shop = relationships["repair_shop"]
    relationship_line = (
        f"This repair shop has {shop['total_claims']} historical claims on file, "
        f"{shop['investigated_claims']} of which were previously investigated."
        if shop.get("repair_shop_id")
        else "No repair shop is associated with this claim."
    )

    return (
        f"Investigation Summary (automated fallback -- LLM unavailable)\n\n"
        f"This claim has a model-generated investigation risk score of "
        f"{ml_result['risk_probability']:.0%} ({ml_result['risk_level']}).\n\n"
        f"Key signals:\n" + "\n".join(signal_lines) + "\n\n"
        f"Relationship context:\n{relationship_line}\n\n"
        f"Recommended verification:\n"
        f"- Review the flagged rule results above against submitted documentation.\n"
        f"- Confirm the repair estimate and incident evidence match the claim description.\n\n"
        f"This is a model-generated risk indicator, not a determination of fraud. "
        f"The final decision belongs to the human investigator."
    )


def generate_investigation_summary(
    system_prompt: str,
    user_prompt: str,
    claim: Dict[str, Any],
    ml_result: Dict[str, Any],
    rule_results: List[Dict[str, Any]],
    relationships: Dict[str, Any],
) -> Dict[str, Any]:
    if os.getenv("OPENAI_API_KEY"):
        try:
            text = _call_openai(system_prompt, user_prompt)
            return {"summary": text, "source": "llm"}
        except Exception as exc:  # noqa: BLE001
            logger.error("OpenAI call failed (%s); using deterministic fallback summary.", exc)

    text = _fallback_summary(claim, ml_result, rule_results, relationships)
    return {"summary": text, "source": "deterministic_fallback"}




"""
    Deteministic rules engine.

    The ML model estimates a learned risk pattern; this modules checks fixed,
    explainable business rules. the two are deliberately kept seperate so a 
    regulator , audotor or investigator can always tell whether a claim was
    flagged because of a hard rule(coverage exceeded, policy expired) or because 
    of a statistical pattern(ML model)

    Every check returns a structured result:
    {"rule" : ... , "status" : "PASS" | "FAIL" | "WARN" , "severity" : "LOW" | "MEDIUM" | "HIGH" , "message" : ...} 
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

from datetime import date ,datetime
from typing import Any, Dict, List 

EARLY_POLICY_DAYS = 30 
HIGH_AMOUNT_RATIO = 0.55

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           Engine Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _parse_date(value) -> date:
    if isinstance(value , date):
        return value 
    return datetime.strptime(str(value)[:10] , "%Y-%m-%d").date()


def check_policy_validity(claim : Dict[str , Any]) -> Dict[str , Any]:
    # Gettting all the dates in proper format
    incident = _parse_date(claim['incident_date'])
    start = _parse_date(claim['policy_start_date'])
    end = _parse_date(claim['policy_end_date'])

    # Check the start should lower then incident and that should lover then end
    # This is the valid case
    if start <= incident <= end:
        return {
            "rule" : "POLICY_VALIDITY",
            "status" : "PASS",
            "severity" : "LOW",
            "message" : "Incident occurred within the policy period."
        }

    # Invalid case
    return {
        "rule" : "POLICY_VALIDITY",
        "status" : "FAIL",
        "severity" : "HIGH",
        "message" : "Incident date falls outside the policy's active period."
    }


def check_coverage_limit(claim : Dict[str , Any]) -> Dict[str , Any]:
    # Getting the data
    amount = float(claim['claim_amount'])
    limit = float(claim['coverage_limit'])

    # check the amount is less then limit or not 
    if amount <= limit:
        return {
            "rule" : "COVERAGE_LIMIT",
            "status" : "PASS",
            "severity" : "LOW",
            "message" : f"Claim amount ({amount:,.0f}) is within the coverage limit ({limit:,.0f})"
        }

    # If amount is higher
    return {
        "rule" : "COVERAGE_LIMIT",
        "status" : "FAIL",
        "severity" : "HIGH",
        "message" : f"Claim amount ({amount:,.0f}) exceed the coverage limit ({limit:,.0f})"
    }


def check_required_documents(claim : Dict[str, Any], submitted_document_types : List[str] = None) -> Dict[str , Any]:
    required = {"CLAIM_FORM", "REGISTRATION", "REPAIR_ESTIMATE"}
    if claim.get("claim_type") == "ACCIDENT":
        required.add("ACCIDENT_EVIDENCE")
    if claim.get("claim_type") == "THEFT":
        required.add("POLICE_REPORT")

    submitted = set(submitted_document_types or [])
    missing = required - submitted
    if not missing:
        return {
            "rule": "REQUIRED_DOCUMENTS",
            "status": "PASS",
            "severity": "LOW",
            "message": "All required documents are on file.",
        }
    
    return {
        "rule": "REQUIRED_DOCUMENTS",
        "status": "WARN",
        "severity": "MEDIUM",
        "message": f"Missing document types: {', '.join(sorted(missing))}.",
    }


def check_early_policy(claim: Dict[str, Any]) -> Dict[str, Any]:
    age = float(claim["policy_age_days"])
    if age >= EARLY_POLICY_DAYS:
        return {
            "rule": "EARLY_POLICY",
            "status": "PASS",
            "severity": "LOW",
            "message": f"Policy was {age:.0f} days old at the time of the claim.",
        }
    return {
        "rule": "EARLY_POLICY",
        "status": "WARN",
        "severity": "MEDIUM",
        "message": f"Policy was only {age:.0f} days old when the claim was filed (threshold: {EARLY_POLICY_DAYS}).",
    }


def check_high_claim_amount(claim: Dict[str, Any]) -> Dict[str, Any]:
    ratio = float(claim["claim_amount"]) / float(claim["vehicle_value"]) if claim.get("vehicle_value") else 0.0
    if ratio <= HIGH_AMOUNT_RATIO:
        return {
            "rule": "HIGH_CLAIM_AMOUNT",
            "status": "PASS",
            "severity": "LOW",
            "message": f"Claim amount is {ratio:.0%} of the vehicle's value.",
        }
    return {
        "rule": "HIGH_CLAIM_AMOUNT",
        "status": "WARN",
        "severity": "MEDIUM",
        "message": f"Claim amount is {ratio:.0%} of the vehicle's value (threshold: {HIGH_AMOUNT_RATIO:.0%}).",
    }



def run_all_rules(claim: Dict[str, Any], submitted_document_types: List[str] = None) -> List[Dict[str, Any]]:
    return [
        check_policy_validity(claim),
        check_coverage_limit(claim),
        check_required_documents(claim, submitted_document_types),
        check_early_policy(claim),
        check_high_claim_amount(claim),
    ]
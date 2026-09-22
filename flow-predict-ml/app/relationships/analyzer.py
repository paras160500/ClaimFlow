"""
    Relationship analysis.

    Answer : "Why does this claim's history matter? by querying ACTUAL database
    relationships == previous claims tied to the same repair shop, vehicle or 
    customer, and their investigation outomes. Nothing here is inventedl every
    number comes from a SQL query against the claims/ investgations tables.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

from typing import Any, Dict, List 
from app.db import get_connection

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           logic Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


def repair_shop_history(repair_shop_id : str , exclude_claim_id : str , limit : int = 10) -> Dict[str , Any]:
    if not repair_shop_id:
        return {"repair_shop_id": None, "total_claims": 0, "investigated_claims": 0, "sample_claims": []}

    with get_connection() as conn:
        totals = conn.execute(
            """
                select
                    count(*) as total_claims,
                    sum(case when investigation_status != 'NOT_FLAGGED' then 1 else 0 end) as investigated_claims
                from claims
                where repair_shop_id = ? and claim_id != ?
            """ , (repair_shop_id , exclude_claim_id)
        ).fetchone()

        sample = conn.execute(
            """
            select claim_id, customer_id, vehicle_id, claim_amount, claim_date, investigation_status
            from claims
            where repair_shop_id = ? and claim_id != ?
            order by claim_date desc
            limit ?
            """, (repair_shop_id, exclude_claim_id, limit),
        ).fetchall()

    return {
        "repair_shop_id": repair_shop_id,
        "total_claims": int(totals["total_claims"] or 0),
        "investigated_claims": int(totals["investigated_claims"] or 0),
        "sample_claims": _rows_to_dicts(sample),
    }


def vehicle_history(vehicle_id: str, exclude_claim_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            select claim_id, claim_type, claim_amount, claim_date, investigation_status
            from claims
            where vehicle_id = ? and claim_id != ?
            order by claim_date desc
            """,
            (vehicle_id, exclude_claim_id),
        ).fetchall()
    return {"vehicle_id": vehicle_id, "total_claims": len(rows), "claims": _rows_to_dicts(rows)}


def customer_history(customer_id : str , exclude_claim_id : str) -> Dict[str , Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
                select claim_id, vehicle_id, claim_type, claim_amount, claim_date, investigation_status
                from claims
                where customer_id = ? and claim_id != ?
                order by claim_date desc
            """ , (customer_id , exclude_claim_id)
        ).fetchall()
    return {"customer_id": customer_id, "total_claims": len(rows), "claims": _rows_to_dicts(rows)}


def investigation_outcomes_for_shop(repair_shop_id : str , exclude_claim_id : str , limit : int = 5) -> List[Dict[str , Any]]:
    if not repair_shop_id:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            """
                select i.investigation_id, i.claim_id, i.status, i.priority, i.reason, i.final_decision
                from investigations i
                join claims c on c.claim_id = i.claim_id
                where c.repair_shop_id = ? and c.claim_id != ?
                order by i.investigation_id desc
                limit ?
            """ , (repair_shop_id , exclude_claim_id , limit)
        ).fetchall()
    return _rows_to_dicts(rows)


def analyze(claim : Dict[str , Any]) -> Dict[str , Any]:
    """
        Full relationship analysis budnle for a single claim, used by the
        /analyze-claim endpoint and returned to the frontend for the
        relationship-visualization view
    """
    claim_id = claim["claim_id"]
    shop = repair_shop_history(claim.get("repair_shop_id"), claim_id)
    vehicle = vehicle_history(claim["vehicle_id"], claim_id)
    customer = customer_history(claim["customer_id"], claim_id)
    shop_investigations = investigation_outcomes_for_shop(claim.get("repair_shop_id"), claim_id)

    return {
        "repair_shop": shop,
        "vehicle": vehicle,
        "customer": customer,
        "repair_shop_investigation_history": shop_investigations,
    }
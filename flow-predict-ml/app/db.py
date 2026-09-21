"""
    Data Access layer for Stage 2

    Stage 1 worked on the CSV training, and this Stage 2 needs real, queryable
    relational data for the relationship-analysis feature ("use actual database 
    relationships...this can initially be implemented using SQL"), and Stage 3
    will point the Node backend at Supabase postgrace using the exact same schema

    Rather than write two versions of every query, this module builds a local
    SQLite mirror of the CSVs generated in Stage 1 and expose a single
    'get_connection()' used by both the rules engine data lookups and the 
    relationship analyszer. The SQL in relationships/analyzer.py is plain
    ANSI-ish SQL that will run on Postgres largely unchanged when stage 3 swaps the connection
    factory for a supabase/psycopg connection.

    Build/refresh the local DB with:
        python scripts/build_local_db.py
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
import sqlite3

DATA_DIR = os.getenv("DATA_DIR" , os.path.join(os.path.dirname(__file__) , ".." , "data"))
DB_PATH = os.path.join(DATA_DIR , "claimflow.db")

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           Connection Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def get_connection() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"local database not found at {DB_PATH}. Run python scripts/build_local_db.py after generating data with datagenerator/generate_data.py"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn 


def fetch_claim_bundle(claim_id : str):
    """
        Returns a dict with the claim joined to its policy, customer,vehicle
        and repair shop -- everything needed to run ML features, rules and to build the LLM prompt
        or None if the claim doesnot exists.
    """
    query = """
        select
            c.claim_id, c.policy_id, c.customer_id, c.vehicle_id, c.repair_shop_id,
            c.claim_date, c.incident_date, c.claim_type, c.claim_amount, c.description,
            c.previous_claim_count, c.days_since_previous_claim, c.customer_claim_frequency,
            c.customer_avg_claim_amount_prior, c.repair_shop_claim_count_prior,
            c.policy_age_days, c.claim_amount_vs_vehicle_value, c.claim_amount_vs_customer_average,
            c.repair_shop_investigation_rate_prior, c.investigation_status, c.status,
            p.coverage_limit, p.deductible, p.start_date as policy_start_date,
            p.end_date as policy_end_date, p.policy_type, p.policy_version_id,
            v.make, v.model, v.manufacture_year, v.vehicle_value,
            cu.full_name as customer_name,
            rs.name as repair_shop_name, rs.city as repair_shop_city
        from claims c
        join policies p on p.policy_id = c.policy_id
        join vehicles v on v.vehicle_id = c.vehicle_id
        join customers cu on cu.customer_id = c.customer_id
        left join repair_shops rs on rs.repair_shop_id = c.repair_shop_id
        where c.claim_id = ?
    """
    with get_connection() as conn:
        row = conn.execute(query , (claim_id , )).fetchone()
        return dict(row) if row else None 
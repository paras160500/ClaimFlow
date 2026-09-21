"""
    Builds a local SQLite database from the CSV produced by
    data_generator/generate_data.py, using (a simplified, SQLite-flavoured
    version of) the same schema as database/schema.sql

    This gives the realtionship analyzer and relies engine real SQL to run against
    before Supabase exists. The table/column names match schema.sql
    so the same SQL mostly works unchanged against Postgres later.

    python scripts/build_local_db.py
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
import sqlite3
import sys 
import pandas as pd 

DATA_DIR = os.getenv("DATA_DIR" , os.path.join(os.path.dirname(__file__) , ".." , "data"))
DB_PATH = os.path.join(DATA_DIR , "claimflow.db")

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Schema generation Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

SCHEMA = """
    create table if not exists repair_shops (
        repair_shop_id text primary key,
        name text, city text, registration_number text, created_at text
    );
    create table if not exists customers (
        customer_id text primary key,
        full_name text, email text, phone text, date_of_birth text, created_at text
    );
    create table if not exists vehicles (
        vehicle_id text primary key,
        customer_id text, make text, model text, manufacture_year int,
        registration_number text, vehicle_value real, created_at text
    );
    create table if not exists policy_versions (
        policy_version_id text primary key,
        policy_type text, version text, effective_from text, effective_to text, description text
    );
    create table if not exists policies (
        policy_id text primary key,
        customer_id text, vehicle_id text, policy_type text, policy_version_id text,
        coverage_limit real, deductible real, start_date text, end_date text, status text
    );
    create table if not exists claims (
        claim_id text primary key,
        policy_id text, customer_id text, vehicle_id text, repair_shop_id text,
        incident_date text, claim_date text, claim_type text, claim_amount real, description text,
        previous_claim_count real, days_since_previous_claim real, customer_claim_frequency real,
        customer_avg_claim_amount_prior real, repair_shop_claim_count_prior real,
        policy_age_days real, claim_amount_vs_vehicle_value real, claim_amount_vs_customer_average real,
        investigation_probability_synthetic real, investigation_label int,
        repair_shop_investigation_rate_prior real, investigation_status text, status text
    );
    create table if not exists investigations (
        investigation_id text primary key,
        claim_id text, status text, priority text, reason text, final_decision text
    );
    create index if not exists idx_claims_repair_shop on claims(repair_shop_id);
    create index if not exists idx_claims_customer on claims(customer_id);
    create index if not exists idx_claims_vehicle on claims(vehicle_id);
    create index if not exists idx_claims_policy on claims(policy_id);
    create index if not exists idx_investigations_claim on investigations(claim_id);
"""

def load_csv(conn , table , filename , dtype = None):
    path = os.path.join(DATA_DIR , filename)
    if not os.path.exists(path):
        print(f"    ! Skippinf {table} : {path} not found")
        return 
    df = pd.read_csv(path , dtype=dtype)
    df.to_sql(table , conn , if_exists="append" , index=False)
    print(f"   loaded {len(df):>6} rows into {table}")


def main():
    if not os.path.isdir(DATA_DIR):
        print(f"Data dir {DATA_DIR} not found. Run data_generator/generate_data.py first")
        sys.exit(1)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    print("Loading CSV into the local SQLite DB")
    load_csv(conn, "repair_shops", "repair_shops.csv")
    load_csv(conn, "customers", "customers.csv")
    load_csv(conn, "vehicles", "vehicles.csv")
    load_csv(conn, "policy_versions", "policy_versions.csv")
    load_csv(conn, "policies", "policies.csv")
    load_csv(conn, "claims", "claims.csv")
    load_csv(conn, "investigations", "investigations.csv")

    conn.commit()
    conn.close()

    print(f"\nDone. Local database written to {DB_PATH}")


if __name__ == "__main__":
    main()
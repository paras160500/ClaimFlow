"""
ClaimFlow synthetic data generator.

Builds a connected, relational insurance ecosystem (not random unrelated rows):

    Customer -> Vehicle -> Policy -> Claim -> Repair Shop

Historical claim-level features (previous_claim_count, days_since_previous_claim,
repair_shop_investigation_rate, etc.) are computed causally: for any given claim,
only claims that happened *before* it are used, exactly like a real feature
pipeline would need to behave to avoid label leakage.

The `investigation_label` (0/1) is a synthetic training target produced from a
weighted COMBINATION of signals plus random noise -- never a single field --
per the project's anti-shortcut requirement. It represents "this historical
claim matched an investigation-worthy pattern", not "this person committed
fraud".

Usage:
    python generate_data.py
    SEED=7 NUM_CLAIMS=5000 python generate_data.py   # smaller/reproducible run
"""


# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import json
import math
import os
import sys

import numpy as np
import pandas as pd
from faker import Faker



# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Generate Table Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

sys.path.insert(0, os.path.dirname(__file__))
from data_generator import config as cfg

def _rng():
    return np.random.default_rng(cfg.SEED)

def generate_repair_shops(rng: np.random.Generator, faker: Faker) -> pd.DataFrame:
    n = cfg.NUM_REPAIR_SHOPS
    is_high_risk = rng.random(n) < cfg.HIGH_RISK_SHOP_FRACTION
    rows = []
    for i in range(n):
        rows.append({
            "repair_shop_id": f"RS{i + 1:05d}",
            "name": f"{faker.last_name()} Auto Works" if i % 2 == 0 else f"{faker.city_prefix()} Motors",
            "city": rng.choice(cfg.CITIES),
            "registration_number": f"REG-RS-{i + 1:05d}",
            # hidden ground-truth propensity, NOT written to the exported table,
            # used only to bias which shops get selected for claims and to bias
            # the investigation label for claims that land at that shop.
            "_is_high_risk": bool(is_high_risk[i]),
        })
    return pd.DataFrame(rows)


def generate_customers(rng: np.random.Generator, faker: Faker) -> pd.DataFrame:
    n = cfg.NUM_CUSTOMERS
    rows = []
    for i in range(n):
        dob = faker.date_of_birth(minimum_age=21, maximum_age=75)
        rows.append({
            "customer_id": f"C{i + 1:06d}",
            "full_name": faker.name(),
            "email": faker.unique.email(),
            "phone": faker.msisdn()[:10],
            "date_of_birth": dob.isoformat(),
        })
    return pd.DataFrame(rows)


def generate_vehicles(rng: np.random.Generator, customers: pd.DataFrame) -> pd.DataFrame:
    n = cfg.NUM_VEHICLES
    customer_ids = customers["customer_id"].values
    # Most customers own 1 vehicle, some own 2-3 -> sample with replacement,
    # weighted so ownership isn't perfectly uniform (more realistic).
    weights = rng.gamma(shape=2.0, scale=1.0, size=len(customer_ids))
    weights = weights / weights.sum()
    owner_ids = rng.choice(customer_ids, size=n, p=weights, replace=True)

    makes = list(cfg.VEHICLE_MAKES_MODELS.keys())
    rows = []
    for i in range(n):
        make = rng.choice(makes)
        model = rng.choice(cfg.VEHICLE_MAKES_MODELS[make])
        year = int(rng.integers(2012, 2026))
        lo, hi = cfg.VEHICLE_VALUE_RANGE[make]
        base_value = rng.uniform(lo, hi)
        age_factor = max(0.35, 1 - (2026 - year) * 0.055)  # depreciate older vehicles
        vehicle_value = round(base_value * age_factor, -3)
        rows.append({
            "vehicle_id": f"V{i + 1:06d}",
            "customer_id": owner_ids[i],
            "make": make,
            "model": model,
            "manufacture_year": year,
            "registration_number": f"REG-V-{i + 1:06d}",
            "vehicle_value": vehicle_value,
        })
    return pd.DataFrame(rows)


def generate_policy_versions() -> pd.DataFrame:
    rows = []
    for pv in cfg.POLICY_VERSIONS:
        rows.append({
            **pv,
            "effective_from": "2018-01-01",
            "effective_to": None,
            "description": f"{pv['policy_type'].title()} insurance policy wording, {pv['version']}.",
        })
    return pd.DataFrame(rows)


def generate_policies(rng: np.random.Generator, vehicles: pd.DataFrame) -> pd.DataFrame:
    n = cfg.NUM_POLICIES
    # sample vehicles (a vehicle can have at most one *active-ish* policy in
    # this simplified generator; sampling without replacement keeps it 1:1
    # while still allowing n < len(vehicles))
    n = min(n, len(vehicles))
    chosen = vehicles.sample(n=n, random_state=cfg.SEED).reset_index(drop=True)

    versions_by_type = {}
    for pv in cfg.POLICY_VERSIONS:
        versions_by_type.setdefault(pv["policy_type"], []).append(pv["policy_version_id"])

    rows = []
    today = pd.Timestamp("2026-09-18")
    for i, veh in chosen.iterrows():
        policy_type = rng.choice(cfg.POLICY_TYPES, p=[0.55, 0.25, 0.10, 0.10])
        policy_version_id = rng.choice(versions_by_type[policy_type])

        # start_date spread over the last ~3 years so claim history can build up
        days_back = int(rng.integers(5, 3 * 365))
        start_date = today - pd.Timedelta(days=days_back)
        end_date = start_date + pd.Timedelta(days=365)

        coverage_limit = round(float(veh["vehicle_value"]) * rng.uniform(0.75, 1.0), -3)
        deductible = round(coverage_limit * rng.uniform(0.01, 0.05), -2)
        status = "ACTIVE" if end_date >= today else "EXPIRED"

        rows.append({
            "policy_id": f"P{i + 1:06d}",
            "customer_id": veh["customer_id"],
            "vehicle_id": veh["vehicle_id"],
            "vehicle_value": veh["vehicle_value"],
            "policy_type": policy_type,
            "policy_version_id": policy_version_id,
            "coverage_limit": coverage_limit,
            "deductible": deductible,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "status": status,
        })
    return pd.DataFrame(rows)


def generate_raw_claims(rng: np.random.Generator, policies: pd.DataFrame,
                         repair_shops: pd.DataFrame, faker: Faker) -> pd.DataFrame:
    n = cfg.NUM_CLAIMS

    # Weighted policy selection so some policies/customers legitimately have
    # multiple historical claims (needed for previous_claim_count etc).
    policy_weights = rng.gamma(shape=1.3, scale=1.0, size=len(policies))
    policy_weights = policy_weights / policy_weights.sum()
    policy_idx = rng.choice(len(policies), size=n, p=policy_weights, replace=True)

    # Weighted repair-shop selection: high-risk shops are over-represented so
    # they accumulate a real, queryable claim history (relationship analysis
    # in later stages depends on this).
    shop_base_weight = rng.gamma(shape=1.0, scale=1.0, size=len(repair_shops))
    shop_base_weight[repair_shops["_is_high_risk"].values] *= 3.5
    shop_weight = shop_base_weight / shop_base_weight.sum()
    shop_idx = rng.choice(len(repair_shops), size=n, p=shop_weight, replace=True)

    claim_types = rng.choice(cfg.CLAIM_TYPES, size=n, p=cfg.CLAIM_TYPE_WEIGHTS)

    rows = []
    for i in range(n):
        pol = policies.iloc[policy_idx[i]]
        shop = repair_shops.iloc[shop_idx[i]]

        policy_start = pd.Timestamp(pol["start_date"])
        policy_end = pd.Timestamp(pol["end_date"])
        span_days = max((policy_end - policy_start).days - 1, 1)
        incident_offset = int(rng.integers(0, span_days))
        incident_date = policy_start + pd.Timedelta(days=incident_offset)
        claim_date = incident_date + pd.Timedelta(days=int(rng.integers(0, 8)))

        vehicle_value = float(pol["vehicle_value"])
        # Most claims are a modest fraction of vehicle value; a deliberate
        # minority are pushed high relative to vehicle value (one of several
        # combined risk signals, not a lone determinant of the label).
        if rng.random() < 0.12:
            amount_ratio = rng.uniform(0.5, 0.95)
        else:
            amount_ratio = float(np.clip(rng.beta(2, 6), 0.02, 0.6))
        claim_amount = round(vehicle_value * amount_ratio, -2)

        rows.append({
            "claim_id": f"CL{i + 1:06d}",
            "policy_id": pol["policy_id"],
            "customer_id": pol["customer_id"],
            "vehicle_id": pol["vehicle_id"],
            "vehicle_value": vehicle_value,
            "repair_shop_id": shop["repair_shop_id"],
            "_shop_is_high_risk": bool(shop["_is_high_risk"]),
            "policy_start_date": pol["start_date"],
            "incident_date": incident_date.date().isoformat(),
            "claim_date": claim_date.date().isoformat(),
            "claim_type": claim_types[i],
            "claim_amount": claim_amount,
            "description": f"{claim_types[i].title()} claim reported for {pol['vehicle_id']}.",
        })

    claims = pd.DataFrame(rows)
    claims["claim_date"] = pd.to_datetime(claims["claim_date"])
    claims["incident_date"] = pd.to_datetime(claims["incident_date"])
    claims["policy_start_date"] = pd.to_datetime(claims["policy_start_date"])
    claims = claims.sort_values("claim_date").reset_index(drop=True)
    return claims


def compute_causal_features(claims: pd.DataFrame) -> pd.DataFrame:
    """
    Adds ML features computed strictly from claims that occurred *before* the
    current one (no leakage from the future), matching how a real online
    feature pipeline / FastAPI feature service would compute them at
    claim-intake time.
    """
    claims = claims.sort_values("claim_date").reset_index(drop=True)

    prev_claim_count = np.zeros(len(claims), dtype=int)
    days_since_prev = np.full(len(claims), -1, dtype=float)  # -1 = no previous claim
    cust_amount_running_mean = np.zeros(len(claims), dtype=float)
    shop_claim_count = np.zeros(len(claims), dtype=int)
    shop_investigated_count = np.zeros(len(claims), dtype=int)
    cust_claim_freq = np.zeros(len(claims), dtype=float)  # claims per 365 days, trailing

    last_claim_date_by_customer = {}
    claim_dates_by_customer = {}
    amounts_by_customer = {}
    claims_by_shop = {}
    investigated_by_shop = {}

    for i, row in claims.iterrows():
        cust = row["customer_id"]
        shop = row["repair_shop_id"]
        this_date = row["claim_date"]

        # --- previous claims for this customer ---
        prev_dates = claim_dates_by_customer.get(cust, [])
        prev_claim_count[i] = len(prev_dates)
        if prev_dates:
            days_since_prev[i] = (this_date - prev_dates[-1]).days
            window_start = this_date - pd.Timedelta(days=365)
            recent = [d for d in prev_dates if d >= window_start]
            cust_claim_freq[i] = len(recent)
        prev_amounts = amounts_by_customer.get(cust, [])
        cust_amount_running_mean[i] = float(np.mean(prev_amounts)) if prev_amounts else row["claim_amount"]

        # --- repair shop history ---
        shop_claim_count[i] = claims_by_shop.get(shop, 0)
        shop_prior = claims_by_shop.get(shop, 0)
        shop_inv_prior = investigated_by_shop.get(shop, 0)

        # update running state AFTER reading (so current claim doesn't leak into itself)
        claim_dates_by_customer.setdefault(cust, []).append(this_date)
        amounts_by_customer.setdefault(cust, []).append(row["claim_amount"])
        claims_by_shop[shop] = shop_prior + 1
        # investigated_by_shop updated later, once labels are known (see below)

    claims["previous_claim_count"] = prev_claim_count
    claims["days_since_previous_claim"] = days_since_prev
    claims["customer_claim_frequency"] = cust_claim_freq
    claims["customer_avg_claim_amount_prior"] = cust_amount_running_mean
    claims["repair_shop_claim_count_prior"] = shop_claim_count

    claims["policy_age_days"] = (claims["claim_date"] - claims["policy_start_date"]).dt.days
    claims["claim_amount_vs_vehicle_value"] = claims["claim_amount"] / claims["vehicle_value"].replace(0, np.nan)
    claims["claim_amount_vs_customer_average"] = (
        claims["claim_amount"] / claims["customer_avg_claim_amount_prior"].replace(0, np.nan)
    ).fillna(1.0)

    return claims


def compute_investigation_label_and_shop_rate(rng: np.random.Generator, claims: pd.DataFrame) -> pd.DataFrame:
    """
    Two-pass process:
      Pass 1: score each claim using a WEIGHTED COMBINATION of signals (never
              a single field) + gaussian noise -> sample a bernoulli label.
      Pass 2: recompute repair_shop_investigation_rate causally, i.e. as of
              each claim's date, using only earlier claims' labels at that shop.
    """
    w = cfg.LABEL_WEIGHTS
    logit = np.full(len(claims), cfg.LABEL_BASE_LOGIT, dtype=float)

    logit += w["early_policy"] * (claims["policy_age_days"] < cfg.EARLY_POLICY_DAYS).astype(float)
    logit += w["high_amount_ratio"] * (claims["claim_amount_vs_vehicle_value"] > cfg.HIGH_AMOUNT_RATIO).astype(float)
    logit += w["many_previous_claims"] * (claims["previous_claim_count"] >= cfg.MANY_PREVIOUS_CLAIMS).astype(float)
    rapid = (claims["days_since_previous_claim"] >= 0) & (claims["days_since_previous_claim"] < cfg.RAPID_RECLAIM_DAYS)
    logit += w["rapid_reclaim"] * rapid.astype(float)
    logit += w["risky_repair_shop"] * claims["_shop_is_high_risk"].astype(float)
    logit += w["high_claim_frequency"] * (claims["customer_claim_frequency"] >= cfg.HIGH_CLAIM_FREQUENCY).astype(float)

    noise = rng.normal(0, cfg.LABEL_NOISE_STD, size=len(claims))
    prob = 1 / (1 + np.exp(-(logit + noise)))
    label = (rng.random(len(claims)) < prob).astype(int)

    claims = claims.copy()
    claims["investigation_probability_synthetic"] = prob
    claims["investigation_label"] = label

    # Now compute the causal repair-shop investigation rate using these labels.
    claims = claims.sort_values("claim_date").reset_index(drop=True)
    shop_seen = {}
    shop_investigated = {}
    rate = np.zeros(len(claims), dtype=float)
    for i, row in claims.iterrows():
        shop = row["repair_shop_id"]
        seen = shop_seen.get(shop, 0)
        inv = shop_investigated.get(shop, 0)
        rate[i] = (inv / seen) if seen > 0 else 0.0
        shop_seen[shop] = seen + 1
        shop_investigated[shop] = inv + int(row["investigation_label"])
    claims["repair_shop_investigation_rate_prior"] = rate

    claims["investigation_status"] = np.where(
        claims["investigation_label"] == 1,
        rng.choice(["FLAGGED", "INVESTIGATED"], size=len(claims), p=[0.35, 0.65]),
        "NOT_FLAGGED",
    )
    claims["status"] = np.where(claims["investigation_status"] == "NOT_FLAGGED", "CLOSED", "UNDER_REVIEW")
    return claims


def build_investigations(rng: np.random.Generator, claims: pd.DataFrame) -> pd.DataFrame:
    flagged = claims[claims["investigation_status"].isin(["FLAGGED", "INVESTIGATED"])].copy()
    decisions = rng.choice(
        ["APPROVE", "REQUEST_DOCUMENTS", "INVESTIGATE_FURTHER", "REJECT"],
        size=len(flagged), p=[0.45, 0.25, 0.20, 0.10],
    )
    reasons = []
    for _, r in flagged.iterrows():
        reason_bits = []
        if r["policy_age_days"] < cfg.EARLY_POLICY_DAYS:
            reason_bits.append("policy created shortly before incident")
        if r["claim_amount_vs_vehicle_value"] > cfg.HIGH_AMOUNT_RATIO:
            reason_bits.append("claim amount high relative to vehicle value")
        if r["previous_claim_count"] >= cfg.MANY_PREVIOUS_CLAIMS:
            reason_bits.append("multiple previous claims on record")
        if 0 <= r["days_since_previous_claim"] < cfg.RAPID_RECLAIM_DAYS:
            reason_bits.append("short interval since previous claim")
        if r["_shop_is_high_risk"]:
            reason_bits.append("repair shop has an elevated historical investigation rate")
        reasons.append("; ".join(reason_bits) if reason_bits else "anomalous pattern flagged by risk model")

    inv = pd.DataFrame({
        "investigation_id": [f"INV{i + 1:06d}" for i in range(len(flagged))],
        "claim_id": flagged["claim_id"].values,
        "status": np.where(flagged["investigation_status"] == "INVESTIGATED", "CLOSED", "IN_PROGRESS"),
        "priority": rng.choice(["LOW", "MEDIUM", "HIGH"], size=len(flagged), p=[0.2, 0.5, 0.3]),
        "reason": reasons,
        "final_decision": np.where(flagged["investigation_status"] == "INVESTIGATED", decisions, None),
    })
    return inv


def inject_demo_scenario(rng, customers, vehicles, policies, claims, repair_shops):
    """
    Rewrites one claim to match the documented demo scenario (Claim CL050001,
    Customer C1024-equivalent, Repair Shop with ~37 historical claims / 5
    investigated) so the UI in later stages has a reliable, presentable demo row.
    Uses whatever real generated shop already has the closest claim-count profile
    rather than fabricating disconnected ids.
    """
    shop_counts = claims.groupby("repair_shop_id").size().sort_values(ascending=False)
    target_shop = shop_counts[(shop_counts >= 25) & (shop_counts <= 60)]
    shop_id = target_shop.index[0] if len(target_shop) else shop_counts.index[0]

    # The demo claim id from the spec (CL050001) only exists if NUM_CLAIMS is
    # large enough; otherwise pick a claim near the 70th-percentile by date
    # and relabel it, so the demo scenario always exists regardless of dataset size.
    demo_row_idx = claims.index[claims["claim_id"] == cfg.DEMO_CLAIM_ID]
    if len(demo_row_idx) == 0:
        fallback_pos = int(len(claims) * 0.7)
        idx = claims.index[fallback_pos]
        if not (claims["claim_id"] == cfg.DEMO_CLAIM_ID).any():
            claims.loc[idx, "claim_id"] = cfg.DEMO_CLAIM_ID
    else:
        idx = demo_row_idx[0]
    vehicle_value = float(claims.loc[idx, "vehicle_value"])
    new_amount = round(vehicle_value * 0.62, -2)
    claims.loc[idx, "repair_shop_id"] = shop_id
    claims.loc[idx, "claim_amount"] = new_amount
    claims.loc[idx, "policy_age_days"] = 18
    claims.loc[idx, "previous_claim_count"] = 4
    claims.loc[idx, "investigation_label"] = 1
    claims.loc[idx, "investigation_status"] = "FLAGGED"
    claims.loc[idx, "status"] = "UNDER_REVIEW"
    # keep derived ratio features consistent with the overwritten fields
    claims.loc[idx, "claim_amount_vs_vehicle_value"] = new_amount / vehicle_value
    prior_avg = float(claims.loc[idx, "customer_avg_claim_amount_prior"]) or new_amount
    claims.loc[idx, "claim_amount_vs_customer_average"] = new_amount / prior_avg
    claims.loc[idx, "repair_shop_investigation_rate_prior"] = 0.135  # ~5 of 37 historical claims
    return claims


def main():
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    rng = _rng()
    faker = Faker()
    Faker.seed(cfg.SEED)

    print(f"[1/8] Generating {cfg.NUM_REPAIR_SHOPS} repair shops...")
    repair_shops = generate_repair_shops(rng, faker)

    print(f"[2/8] Generating {cfg.NUM_CUSTOMERS} customers...")
    customers = generate_customers(rng, faker)

    print(f"[3/8] Generating {cfg.NUM_VEHICLES} vehicles...")
    vehicles = generate_vehicles(rng, customers)

    print("[4/8] Generating policy versions...")
    policy_versions = generate_policy_versions()

    print(f"[5/8] Generating {cfg.NUM_POLICIES} policies...")
    policies = generate_policies(rng, vehicles)

    print(f"[6/8] Generating {cfg.NUM_CLAIMS} claims (raw, then causal features)...")
    claims = generate_raw_claims(rng, policies, repair_shops, faker)
    claims = compute_causal_features(claims)

    print("[7/8] Scoring synthetic investigation_label + repair-shop history...")
    claims = compute_investigation_label_and_shop_rate(rng, claims)
    claims = inject_demo_scenario(rng, customers, vehicles, policies, claims, repair_shops)

    print("[8/8] Building investigations table + writing output files...")
    investigations = build_investigations(rng, claims)

    # Clean up helper/internal columns before export
    export_claims = claims.drop(columns=["_shop_is_high_risk", "vehicle_value", "policy_start_date"])
    export_repair_shops = repair_shops.drop(columns=["_is_high_risk"])

    customers.to_csv(f"{cfg.OUTPUT_DIR}/customers.csv", index=False)
    vehicles.to_csv(f"{cfg.OUTPUT_DIR}/vehicles.csv", index=False)
    export_repair_shops.to_csv(f"{cfg.OUTPUT_DIR}/repair_shops.csv", index=False)
    policy_versions.to_csv(f"{cfg.OUTPUT_DIR}/policy_versions.csv", index=False)
    policies.drop(columns=["vehicle_value"]).to_csv(f"{cfg.OUTPUT_DIR}/policies.csv", index=False)
    export_claims.to_csv(f"{cfg.OUTPUT_DIR}/claims.csv", index=False)
    investigations.to_csv(f"{cfg.OUTPUT_DIR}/investigations.csv", index=False)

    summary = {
        "seed": cfg.SEED,
        "counts": {
            "customers": len(customers),
            "vehicles": len(vehicles),
            "repair_shops": len(repair_shops),
            "policies": len(policies),
            "claims": len(claims),
            "investigations": len(investigations),
        },
        "investigation_label_positive_rate": round(float(claims["investigation_label"].mean()), 4),
        "high_risk_repair_shop_fraction_actual": round(float(repair_shops["_is_high_risk"].mean()), 4),
    }
    with open(f"{cfg.OUTPUT_DIR}/generation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDone. Summary:")
    print(json.dumps(summary, indent=2))
    print(f"\nFiles written to ./{cfg.OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

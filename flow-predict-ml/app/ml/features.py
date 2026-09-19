"""
    Feature engineering shared between offline training and online
    inference via fastapi to pridict.

    This file guarantees train and predict will get the same features
    for training and predicting.

    Deliberatly excluded from features: customer name , email , phone and any
    other identifying but non predictive field
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
from typing import Any,Dict,List 

import numpy as np
import pandas as pd 


# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           Features Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

FEATURE_COLUMNS : List[str] = [
    "claim_amount",
    "policy_age_days",
    "vehicle_age",
    "previous_claim_count",
    "days_since_previous_claim",
    "customer_claim_frequency",
    "repair_shop_claim_count_prior",
    "repair_shop_investigation_rate_prior",
    "claim_amount_vs_vehicle_value",
    "claim_amount_vs_customer_average",
]

TARGET_COLUMN = "investigation_label"

CURRENT_YEAR = 2026


def build_training_frame(claims : pd.DataFrame , vehicles : pd.DataFrame) -> pd.DataFrame:
    """
        Joins claims.csv with vehicles.csv (for manufacture_year -> vehicle_age)
        and return a frame with exactly FEATURE_COLUMNS + TRAGET_COLUMN, ready
        for train/test split
    """
    df = claims.merge(
        vehicles[['vehicle_id' , "manufacture_year"]],
        on="vehicle_id",
        how="left"
    )
    df['vehicle_age'] = CURRENT_YEAR - df['manufacture_year']

    # days_since_previous_claim uses -1 as a sentinel for "no previous claims" in
    # the raw data; that is valid, inforamtive numeric value for tree models.
    # So we leave it rather than imputing it away.
    df['days_since_previous_claim'] = df['days_since_previous_claim'].fillna(-1)

    frame = df[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()
    frame = frame.replace([np.inf , -np.inf] , np.nan)
    frame = frame.dropna(subset = FEATURE_COLUMNS + [TARGET_COLUMN])
    return frame 


def build_feature_row_from_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    """
    Builds a single-row feature frame for online inference from a raw feature
    payload (see app/schemas/claim.py for the expected shape). Missing
    optional fields default to conservative, low-risk values.
    """
    row = {
        "claim_amount": float(payload["claim_amount"]),
        "policy_age_days": float(payload["policy_age_days"]),
        "vehicle_age": float(payload.get("vehicle_age", 5)),
        "previous_claim_count": float(payload.get("previous_claim_count", 0)),
        "days_since_previous_claim": float(payload.get("days_since_previous_claim", -1)),
        "customer_claim_frequency": float(payload.get("customer_claim_frequency", 0)),
        "repair_shop_claim_count_prior": float(payload.get("repair_shop_claim_count_prior", 0)),
        "repair_shop_investigation_rate_prior": float(payload.get("repair_shop_investigation_rate_prior", 0.0)),
        "vehicle_value": float(payload.get("vehicle_value", 0)) or None,
        "customer_avg_claim_amount_prior": float(payload.get("customer_avg_claim_amount_prior", 0)) or None,
    }

    vehicle_value = payload.get("vehicle_value")
    row["claim_amount_vs_vehicle_value"] = (
        row["claim_amount"] / vehicle_value if vehicle_value else 0.0
    )
    prior_avg = payload.get("customer_avg_claim_amount_prior")
    row["claim_amount_vs_customer_average"] = (
        row["claim_amount"] / prior_avg if prior_avg else 1.0
    )

    ordered = {col: row[col] for col in FEATURE_COLUMNS}
    return pd.DataFrame([ordered])



def risk_level_from_probability(probability: float, thresholds=(0.40, 0.70)) -> str:
    low_high, high_cut = thresholds
    if probability < low_high:
        return "LOW"
    if probability < high_cut:
        return "MEDIUM"
    return "HIGH"
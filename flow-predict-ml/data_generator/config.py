"""
    Configuration for the ClaimFlow synthetic data generator

    Every volume/threshould here is intentionally centralised so the dataset
    size and risk pattern strength can be tuned without touching generation logic.
    All of this Synthetic data manufactured for this project only.
    This does not represent any real insurer, custoemr or claim.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
SEED = int(os.getenv("SEED" , "42"))

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                           Data Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Volumes can be override as per the data requirements.
NUM_CUSTOMERS = int(os.getenv("NUM_CUSTOMERS", "10000"))
NUM_VEHICLES = int(os.getenv("NUM_VEHICLES", "15000"))
NUM_REPAIR_SHOPS = int(os.getenv("NUM_REPAIR_SHOPS", "500"))
NUM_POLICIES = int(os.getenv("NUM_POLICIES", "12000"))
NUM_CLAIMS = int(os.getenv("NUM_CLAIMS", "30000"))


# Output path for generated csv
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")


# Reference Data 
VEHICLE_MAKES_MODELS = {
    "Maruti Suzuki": ["Swift", "Baleno", "Dzire", "Ertiga", "Brezza"],
    "Hyundai": ["i20", "Creta", "Venue", "Verna", "i10"],
    "Tata": ["Nexon", "Punch", "Harrier", "Altroz", "Tiago"],
    "Honda": ["City", "Amaze", "Civic"],
    "Toyota": ["Innova", "Fortuner", "Glanza"],
    "Mahindra": ["XUV700", "Scorpio", "Bolero", "XUV300"],
    "Kia": ["Seltos", "Sonet", "Carens"],
    "Volkswagen": ["Polo", "Virtus", "Taigun"],
}


# Base ex-showroom-ish value ranges per make (INR), used to derive vehicle_value
VEHICLE_VALUE_RANGE = {
    "Maruti Suzuki": (500_000, 1_100_000),
    "Hyundai": (700_000, 1_600_000),
    "Tata": (600_000, 1_800_000),
    "Honda": (900_000, 1_900_000),
    "Toyota": (1_200_000, 3_800_000),
    "Mahindra": (900_000, 2_800_000),
    "Kia": (900_000, 2_200_000),
    "Volkswagen": (900_000, 2_100_000),
}


# Type of Policies
POLICY_TYPES = ["COMPREHENSIVE", "THIRD_PARTY", "THEFT", "COMMERCIAL"]


# Version of the Policies
POLICY_VERSIONS = [
    {"policy_version_id": "PV-COMP-V1", "policy_type": "COMPREHENSIVE", "version": "V1"},
    {"policy_version_id": "PV-COMP-V2", "policy_type": "COMPREHENSIVE", "version": "V2"},
    {"policy_version_id": "PV-TP-V1", "policy_type": "THIRD_PARTY", "version": "V1"},
    {"policy_version_id": "PV-THEFT-V1", "policy_type": "THEFT", "version": "V1"},
    {"policy_version_id": "PV-COMM-V1", "policy_type": "COMMERCIAL", "version": "V1"},
]


# Claim Types
CLAIM_TYPES = ["ACCIDENT", "THEFT", "FIRE", "NATURAL_DISASTER", "VANDALISM"]


# Claim Type weights
CLAIM_TYPE_WEIGHTS = [0.65, 0.12, 0.06, 0.10, 0.07]


# Cities
CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Ahmedabad",
    "Chennai", "Pune", "Vadodara", "Surat", "Jaipur",
]


# Risk shop Configuration
# A minority of repair shops are deliberately given a much higher long-run
# association with investigation-pattern claims, and are also over-weighted
# in claim assignment so they build up a real, queryable claim history.
HIGH_RISK_SHOP_FRACTION = 0.08


# ---- Investigation-label scoring weights ----
# The label is a probabilistic combination of signals (never a single field),
# matching the "no single-field determines the label" requirement.
LABEL_WEIGHTS = {
    "early_policy": 1.4,          # policy_age_days < EARLY_POLICY_DAYS
    "high_amount_ratio": 1.6,     # claim_amount / vehicle_value > HIGH_AMOUNT_RATIO
    "many_previous_claims": 1.1,  # previous_claim_count >= MANY_PREVIOUS_CLAIMS
    "rapid_reclaim": 1.3,         # days_since_previous_claim < RAPID_RECLAIM_DAYS
    "risky_repair_shop": 1.5,     # repair shop flagged as high-risk
    "high_claim_frequency": 0.9,  # customer_claim_frequency high
}


LABEL_BASE_LOGIT = -4.6  # keeps overall positive rate roughly in a realistic 8-15% band
LABEL_NOISE_STD = 0.6

EARLY_POLICY_DAYS = 30
HIGH_AMOUNT_RATIO = 0.55
MANY_PREVIOUS_CLAIMS = 3
RAPID_RECLAIM_DAYS = 30
HIGH_CLAIM_FREQUENCY = 3  # claims per customer per year-equivalent, approx

# Demo scenario claim id / codes referenced in docs and UI
DEMO_CLAIM_ID = "CL050001"

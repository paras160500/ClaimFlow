"""
    Builds the small synthetic policy knowledge base(one doc per policy
    type/version , not one per policy number) and a set of historical 
    investigator notes derived from the generated investigations/claims data.

    python knowledge_base/build_knowledge_base.py

    Output:
        will generate policy_doc folder having all the policy documents
        will generate investigator_notes folder having all the notes for the investigators
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
import sys 
import pandas as pd 

BASE_DIR = os.path.dirname(__file__)
POLICY_DIR = os.path.join(BASE_DIR, "policy_docs")
NOTES_DIR = os.path.join(BASE_DIR, "investigator_notes")
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "..", "data"))

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Knowledge base creation Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

POLICY_DOCS = {
    "comprehensive_v2.txt": """Policy Type: Comprehensive Vehicle Insurance
    Version: V2

    Coverage:
    This version extends V1 coverage to include roadside assistance and a
    no-claim-bonus protection add-on for policyholders with three or more
    consecutive claim-free years. Core coverage for accidental damage, fire,
    natural disaster, vandalism, and theft remains unchanged from V1.

    Required documents:
    Same document requirements as V1: completed claim form, vehicle registration,
    repair estimate, and incident evidence. Theft claims require a police report.

    Exclusions:
    Same exclusions as V1. Additionally, roadside-assistance callouts unrelated
    to an insured event are not covered under the comprehensive claim process.

    Claim amount guidance:
    Same guidance as V1. The no-claim-bonus protection add-on does not change
    claim-amount review standards.
    """,

# ---------------------------------------------------------------------------------------

    "third_party_v1.txt": """Policy Type: Third-Party Vehicle Insurance
    Version: V1

    Coverage:
    Covers legal liability for injury to third parties and damage to third-party
    property caused by the insured vehicle. Does NOT cover damage to the insured
    vehicle itself.

    Required documents:
    Required documents include the completed claim form, vehicle registration,
    a copy of the third-party's damage assessment or repair estimate, and an
    incident report describing how the third-party loss occurred.

    Exclusions:
    Damage to the insured vehicle is excluded (see Comprehensive policies for
    own-damage coverage). Claims arising outside the policy period are excluded.
    Intentional acts are excluded.

    Claim amount guidance:
    Claim amounts should be supported by an independent assessment of third-party
    loss. Claims without a corroborating third-party report should be flagged for
    additional documentation before processing.
    """,

# ---------------------------------------------------------------------------------------

    "theft_v1.txt": """Policy Type: Theft Insurance
    Version: V1

    Coverage:
    Covers total loss of the insured vehicle due to theft, up to the vehicle's
    assessed value at the time of loss. Partial theft of vehicle parts is
    covered up to a sub-limit specified on the policy schedule.

    Required documents:
    A police report filed within 48 hours of discovery is mandatory. Required
    documents also include the completed claim form, vehicle registration,
    original key(s), and, where available, GPS/tracking device logs.

    Exclusions:
    Theft is excluded if the vehicle was left unlocked or with keys accessible
    in a public place, or if the theft is not reported to police within the
    required window. Theft by a family member or authorized driver is handled
    under a separate investigation process rather than a standard theft payout.

    Claim amount guidance:
    Claims should reflect the vehicle's assessed market value at the time of
    loss, adjusted for age, condition, and mileage where known. A theft claim
    filed shortly after policy inception, or shortly after a change of
    registered owner, should be reviewed against the vehicle's full ownership
    and policy history before payout.
    """,

# ---------------------------------------------------------------------------------------

    "commercial_v1.txt": """Policy Type: Commercial Vehicle Insurance
    Version: V1

    Coverage:
    Covers vehicles used for commercial/fleet purposes, including goods
    transport and passenger transport. Coverage includes accidental damage,
    fire, natural disaster, theft, and third-party liability arising from
    commercial use.

    Required documents:
    Required documents include the completed claim form, vehicle registration,
    commercial permit/license documentation, a repair estimate, and (for
    transport-related incidents) a trip log or waybill covering the incident
    period.

    Exclusions:
    Use of the vehicle outside the licensed commercial purpose (e.g. unauthorized
    personal use) is excluded. Overloading beyond the vehicle's rated capacity at
    the time of the incident is excluded. Damage occurring outside the policy
    period is not covered.

    Claim amount guidance:
    Given higher average claim values in commercial fleets, claims should be
    cross-checked against maintenance records and, where the claim amount is a
    large fraction of the vehicle's assessed value, against the trip log to
    confirm the vehicle was in authorized commercial use at the time of the
    incident.
    """,
}


def write_policy_docs():
    os.makedirs(POLICY_DIR , exist_ok= True)
    for filename , content in POLICY_DOCS.items():
        path = os.path.join(POLICY_DIR , filename)
        with open(path , "w") as f:
            f.write(content)

    print(f"Wrote {len(POLICY_DOCS)} generated policiy docs to {POLICY_DIR} ")
    print(f"Also comprehensize_v1.txt committed seperately.")


NOTE_TEMPLATES = [
    (
        lambda r: r["policy_age_days"] < 30,
        "The policy on claim {claim_id} was only {policy_age_days:.0f} days old when the "
        "claim was filed. The investigator requested the original policy application and "
        "confirmed there was no prior coverage gap before proceeding.",
    ),
    (
        lambda r: r["claim_amount_vs_vehicle_value"] > 0.55,
        "Claim {claim_id} was reviewed because the claimed repair amount was significantly "
        "high relative to the vehicle's assessed value. The investigator requested an "
        "independent repair estimate for comparison.",
    ),
    (
        lambda r: r["previous_claim_count"] >= 3,
        "The customer on claim {claim_id} had {previous_claim_count:.0f} previous claims on "
        "file. The investigator cross-referenced the claim history and found the pattern "
        "consistent with the customer's usage profile.",
    ),
    (
        lambda r: 0 <= r["days_since_previous_claim"] < 30,
        "Claim {claim_id} was filed only {days_since_previous_claim:.0f} days after the "
        "customer's previous claim. The investigator confirmed the two incidents were "
        "unrelated based on the incident descriptions and repair shop records.",
    ),
    (
        lambda r: r["repair_shop_investigation_rate_prior"] > 0.1,
        "The repair shop associated with claim {claim_id} has an elevated historical "
        "investigation rate. The investigator requested the original repair invoice "
        "directly from the shop rather than relying on the submitted estimate alone.",
    ),
]

DEFAULT_TEMPLATE = (
    "Claim {claim_id} was flagged for standard review. The investigator confirmed the "
    "submitted documentation matched the reported incident and proceeded with the "
    "standard investigation checklist."
)


def build_note_text(row) -> str:
    lines = [f"Investigation Note -- Claim {row['claim_id']}", ""]
    matched_any = False
    for condition, template in NOTE_TEMPLATES:
        try:
            if condition(row):
                lines.append(template.format(**row))
                matched_any = True
        except Exception:
            continue
    if not matched_any:
        lines.append(DEFAULT_TEMPLATE.format(claim_id=row["claim_id"]))

    decision = row.get("final_decision")
    if isinstance(decision, str) and decision:
        decision_text = {
            "APPROVE": "The claim was ultimately approved after review.",
            "REQUEST_DOCUMENTS": "Additional documents were requested from the claimant before a decision could be made.",
            "INVESTIGATE_FURTHER": "The claim was escalated for further investigation.",
            "REJECT": "The claim was rejected following the investigation.",
        }.get(decision, "")
        if decision_text:
            lines.append(decision_text)

    return "\n".join(lines) + "\n"


def build_investigator_notes(max_notes: int = 300, seed: int = 42):
    os.makedirs(NOTES_DIR, exist_ok=True)
    claims_path = os.path.join(DATA_DIR, "claims.csv")
    investigations_path = os.path.join(DATA_DIR, "investigations.csv")
    if not (os.path.exists(claims_path) and os.path.exists(investigations_path)):
        print(f"claims.csv / investigations.csv not found in {DATA_DIR}. "
              "Run data_generator/generate_data.py first.")
        sys.exit(1)

    claims = pd.read_csv(claims_path)
    investigations = pd.read_csv(investigations_path)

    merged = investigations.merge(claims, on="claim_id", how="left")
    if len(merged) > max_notes:
        merged = merged.sample(n=max_notes, random_state=seed)

    written = 0
    for _, row in merged.iterrows():
        text = build_note_text(row)
        path = os.path.join(NOTES_DIR, f"{row['claim_id']}.txt")
        with open(path, "w") as f:
            f.write(text)
        written += 1

    print(f"Wrote {written} investigator notes to {NOTES_DIR}")




if __name__ == "__main__":
    write_policy_docs()
    build_investigator_notes()
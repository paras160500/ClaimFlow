/**
 * SeedSupabaseCSV to the Server
 * Below is the content which can take us to 
 */

require("dotenv").config();
const { parse } = require("csv-parse/sync");
const { readFileSync, existsSync } = require("fs");
const path = require("path");
const { supabaseAdmin } = require("../src/database/supabase");

const CSV_DIR = process.env.CSV_DATA_DIR || path.join(__dirname, "..", "..", "flow-predict-ml", "data");
const BATCH_SIZE = 500;

function readCsv(filename) {
  const filePath = path.join(CSV_DIR, filename);
  if (!existsSync(filePath)) {
    console.log(`  ! skipping ${filename}: not found at ${filePath}`);
    return [];
  }
  const raw = readFileSync(filePath, "utf-8");
  return parse(raw, { columns: true, skip_empty_lines: true });
}

function toNum(value) {
  if (value === undefined || value === "" || value === "None") return null;
  const n = Number(value);
  return Number.isNaN(n) ? null : n;
}

function toStrOrNull(value) {
  return value === undefined || value === "" || value === "None" ? null : value;
}

async function upsertInBatches(table, rows, conflictColumn) {
  if (rows.length === 0) {
    console.log(`  ${table}: 0 rows (nothing to do)`);
    return;
  }
  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const batch = rows.slice(i, i + BATCH_SIZE);
    const { error } = await supabaseAdmin.from(table).upsert(batch, { onConflict: conflictColumn });
    if (error) {
      throw new Error(`Failed to upsert into ${table} (batch starting at ${i}): ${error.message}`);
    }
  }
  console.log(`  ${table}: upserted ${rows.length} rows`);
}

async function main() {
  console.log(`Reading CSVs from: ${CSV_DIR}\n`);

  // Order matters: parents before children, to satisfy foreign keys.
  const repairShops = readCsv("repair_shops.csv").map((r) => ({
    repair_shop_id: r.repair_shop_id,
    name: r.name,
    city: r.city,
    registration_number: r.registration_number,
  }));
  await upsertInBatches("repair_shops", repairShops, "repair_shop_id");

  const customers = readCsv("customers.csv").map((r) => ({
    customer_id: r.customer_id,
    full_name: r.full_name,
    email: r.email,
    phone: r.phone,
    date_of_birth: r.date_of_birth,
  }));
  await upsertInBatches("customers", customers, "customer_id");

  const vehicles = readCsv("vehicles.csv").map((r) => ({
    vehicle_id: r.vehicle_id,
    customer_id: r.customer_id,
    make: r.make,
    model: r.model,
    manufacture_year: toNum(r.manufacture_year),
    registration_number: r.registration_number,
    vehicle_value: toNum(r.vehicle_value),
  }));
  await upsertInBatches("vehicles", vehicles, "vehicle_id");

  const policyVersions = readCsv("policy_versions.csv").map((r) => ({
    policy_version_id: r.policy_version_id,
    policy_type: r.policy_type,
    version: r.version,
    effective_from: r.effective_from,
    effective_to: toStrOrNull(r.effective_to),
    description: r.description,
  }));
  await upsertInBatches("policy_versions", policyVersions, "policy_version_id");

  const policies = readCsv("policies.csv").map((r) => ({
    policy_id: r.policy_id,
    customer_id: r.customer_id,
    vehicle_id: r.vehicle_id,
    policy_type: r.policy_type,
    policy_version_id: r.policy_version_id,
    coverage_limit: toNum(r.coverage_limit),
    deductible: toNum(r.deductible),
    start_date: r.start_date,
    end_date: r.end_date,
    status: r.status,
  }));
  await upsertInBatches("policies", policies, "policy_id");

  // Only the columns that exist in the real `claims` table (schema.sql) --
  // see the file header comment for why the rest of claims.csv is dropped.
  const claims = readCsv("claims.csv").map((r) => ({
    claim_id: r.claim_id,
    policy_id: r.policy_id,
    customer_id: r.customer_id,
    vehicle_id: r.vehicle_id,
    repair_shop_id: toStrOrNull(r.repair_shop_id),
    claim_date: r.claim_date,
    incident_date: r.incident_date,
    claim_type: r.claim_type,
    claim_amount: toNum(r.claim_amount),
    description: r.description,
    status: r.status,
    investigation_status: r.investigation_status,
    investigation_label: toNum(r.investigation_label),
  }));
  await upsertInBatches("claims", claims, "claim_id");

  const investigations = readCsv("investigations.csv").map((r) => ({
    investigation_id: r.investigation_id,
    claim_id: r.claim_id,
    status: r.status,
    priority: r.priority,
    reason: r.reason,
    final_decision: toStrOrNull(r.final_decision),
  }));
  await upsertInBatches("investigations", investigations, "investigation_id");

  console.log("\nDone. Supabase now has the same demo dataset as the AI service's local database.");
}

main().catch((err) => {
  console.error("Seeding failed:", err.message);
  process.exit(1);
});
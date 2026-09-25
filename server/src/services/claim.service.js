/**
 * Every query here goes through supabaseadmin because by the time a request reaches 
 * this service all middleware already decided whether the caller is allowed to be
 * here or not.
 */

const { supabaseAdmin } = require("../database/supabase");
const { AppError } = require("../utils/AppError");

const CLAIM_SELECT = `
  claim_id, policy_id, customer_id, vehicle_id, repair_shop_id,
  claim_date, incident_date, claim_type, claim_amount, description,
  status, investigation_status, investigation_label, created_at,
  policies ( policy_type, policy_version_id, coverage_limit, deductible, start_date, end_date, status ),
  customers ( full_name, email, phone ),
  vehicles ( make, model, manufacture_year, vehicle_value ),
  repair_shops ( name, city )
`;

async function listClaims(filters) {
  let query = supabaseAdmin.from("claims").select(CLAIM_SELECT, { count: "exact" });

  if (filters.status) query = query.eq("status", filters.status);
  if (filters.investigationStatus) query = query.eq("investigation_status", filters.investigationStatus);
  if (filters.claimType) query = query.eq("claim_type", filters.claimType);
  if (filters.search) {
    // Matches on claim id, policy id, or vehicle id -- customer-name search
    // would need a join-aware `.or()`, which PostgREST doesn't support
    // across embedded tables, so that's left for a future improvement.
    query = query.or(
      `claim_id.ilike.%${filters.search}%,policy_id.ilike.%${filters.search}%,vehicle_id.ilike.%${filters.search}%`
    );
  }

  const page = filters.page || 1;
  const pageSize = filters.pageSize || 20;
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;
  query = query.order("claim_date", { ascending: false }).range(from, to);

  const { data, error, count } = await query;
  if (error) throw new AppError(`Failed to list claims: ${error.message}`, 500);

  return { claims: data || [], total: count || 0, page, pageSize };
}

async function getClaimById(claimId) {
  const { data, error } = await supabaseAdmin
    .from("claims")
    .select(CLAIM_SELECT)
    .eq("claim_id", claimId)
    .maybeSingle();

  if (error) throw new AppError(`Failed to fetch claim: ${error.message}`, 500);
  if (!data) throw new AppError(`No claim found with id ${claimId}`, 404);
  return data;
}

async function createClaim(payload) {
  const { data, error } = await supabaseAdmin
    .from("claims")
    .insert({ ...payload, status: "SUBMITTED", investigation_status: "NOT_FLAGGED" })
    .select()
    .single();

  if (error) throw new AppError(`Failed to create claim: ${error.message}`, 400);
  return data;
}

/** Used if you build a route around /api/predict directly, without the full analyze pipeline. */
async function getClaimFeatureInputs(claimId) {
  const claim = await getClaimById(claimId);
  const policy = claim.policies;
  const vehicle = claim.vehicles;

  if (!policy || !vehicle) {
    throw new AppError("Claim is missing a linked policy or vehicle; cannot compute features.", 422);
  }

  const policyAgeDays = Math.floor(
    (new Date(claim.claim_date).getTime() - new Date(policy.start_date).getTime()) / 86_400_000
  );
  const vehicleAge = new Date().getFullYear() - vehicle.manufacture_year;

  return {
    claim_id: claim.claim_id,
    claim_amount: claim.claim_amount,
    policy_age_days: policyAgeDays,
    vehicle_age: vehicleAge,
    vehicle_value: vehicle.vehicle_value,
  };
}

module.exports = { listClaims, getClaimById, createClaim, getClaimFeatureInputs };
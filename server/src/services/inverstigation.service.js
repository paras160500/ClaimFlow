const { supabaseAdmin } = require("../database/supabase");
const { AppError } = require("../utils/AppError");

async function listInvestigations(filters) {
  let query = supabaseAdmin
    .from("investigations")
    .select("*, claims ( claim_id, claim_amount, claim_type, status, investigation_status )", {
      count: "exact",
    });

  if (filters.status) query = query.eq("status", filters.status);
  if (filters.priority) query = query.eq("priority", filters.priority);
  if (filters.assignedTo) query = query.eq("assigned_to", filters.assignedTo);

  const page = filters.page || 1;
  const pageSize = filters.pageSize || 20;
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;
  query = query.order("created_at", { ascending: false }).range(from, to);

  const { data, error, count } = await query;
  if (error) throw new AppError(`Failed to list investigations: ${error.message}`, 500);
  return { investigations: data || [], total: count || 0, page, pageSize };
}

async function getInvestigationByClaim(claimId) {
  const { data, error } = await supabaseAdmin
    .from("investigations")
    .select("*")
    .eq("claim_id", claimId)
    .order("created_at", { ascending: false });

  if (error) throw new AppError(`Failed to fetch investigations: ${error.message}`, 500);
  return data || [];
}

/**
 * This is where a human investigator's decision actually gets written down
 * -- the one moment in the whole system where an AI-generated risk score
 * turns into a real business outcome. This function only ever WRITES a
 * decision a person made; it never computes one.
 */
async function recordDecision(investigationId, employeeEmail, decision, note) {
  const { data: investigation, error: fetchError } = await supabaseAdmin
    .from("investigations")
    .select("*")
    .eq("investigation_id", investigationId)
    .maybeSingle();

  if (fetchError) throw new AppError(`Failed to fetch investigation: ${fetchError.message}`, 500);
  if (!investigation) throw new AppError(`No investigation found with id ${investigationId}`, 404);

  const existingNotes = investigation.investigator_notes ? `${investigation.investigator_notes}\n` : "";
  const timestampedNote = note
    ? `${existingNotes}[${new Date().toISOString()}] ${employeeEmail}: ${note}`
    : existingNotes;

  const { data, error } = await supabaseAdmin
    .from("investigations")
    .update({
      final_decision: decision,
      investigator_notes: timestampedNote || null,
      status: "CLOSED",
      assigned_to: investigation.assigned_to || employeeEmail,
      updated_at: new Date().toISOString(),
    })
    .eq("investigation_id", investigationId)
    .select()
    .single();

  if (error) throw new AppError(`Failed to record decision: ${error.message}`, 500);

  // Reflect the outcome on the claim itself so claim lists/filters stay in sync.
  await supabaseAdmin
    .from("claims")
    .update({ investigation_status: "INVESTIGATED", status: "CLOSED" })
    .eq("claim_id", investigation.claim_id);

  return data;
}

module.exports = { listInvestigations, getInvestigationByClaim, recordDecision };
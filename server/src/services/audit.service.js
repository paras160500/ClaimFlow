const { supabaseAdmin } = require("../database/supabase");

async function writeAuditLog(params) {
  const { error } = await supabaseAdmin.from("audit_logs").insert({
    employee_id: params.employeeId,
    claim_id: params.claimId || null,
    action: params.action,
    details: params.details || null,
  });

  if (error) {
    // Deliberately non-fatal: a logging failure should never block the
    // actual user-facing action (viewing a claim, saving a decision, etc.)
    console.error("[audit] failed to write audit log:", error.message);
  }
}

async function listAuditLogs(params) {
  let query = supabaseAdmin.from("audit_logs").select("*", { count: "exact" });
  if (params.claimId) query = query.eq("claim_id", params.claimId);
  if (params.employeeId) query = query.eq("employee_id", params.employeeId);

  const page = params.page || 1;
  const pageSize = params.pageSize || 25;
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;
  query = query.order("created_at", { ascending: false }).range(from, to);

  const { data, error, count } = await query;
  if (error) throw error;
  return { logs: data || [], total: count || 0, page, pageSize };
}

module.exports = { writeAuditLog, listAuditLogs };
/**
 * These are plain counting queries, deliberately kept as seprate simple
 * calls rather than on clever SQL function
 */

const { supabaseAdmin } = require("../database/supabase");

async function getDashboardStats() {
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);

  const [totalClaims, flaggedClaims, highRiskAssessments, pendingInvestigations, reviewedToday] =
    await Promise.all([
      supabaseAdmin.from("claims").select("*", { count: "exact", head: true }),
      supabaseAdmin
        .from("claims")
        .select("*", { count: "exact", head: true })
        .in("investigation_status", ["FLAGGED", "INVESTIGATED"]),
      supabaseAdmin
        .from("ml_assessments")
        .select("claim_id", { count: "exact", head: true })
        .eq("risk_level", "HIGH"),
      supabaseAdmin
        .from("investigations")
        .select("*", { count: "exact", head: true })
        .in("status", ["OPEN", "IN_PROGRESS"]),
      supabaseAdmin
        .from("investigations")
        .select("*", { count: "exact", head: true })
        .eq("status", "CLOSED")
        .gte("updated_at", todayStart.toISOString()),
    ]);

  return {
    total_claims: totalClaims.count || 0,
    claims_requiring_investigation: flaggedClaims.count || 0,
    high_risk_claims: highRiskAssessments.count || 0,
    pending_investigations: pendingInvestigations.count || 0,
    claims_reviewed_today: reviewedToday.count || 0,
  };
}

async function getRiskDistribution() {
  const { data, error } = await supabaseAdmin.from("ml_assessments").select("risk_level");
  if (error || !data) return { LOW: 0, MEDIUM: 0, HIGH: 0 };

  return data.reduce(
    (acc, row) => {
      acc[row.risk_level] = (acc[row.risk_level] || 0) + 1;
      return acc;
    },
    { LOW: 0, MEDIUM: 0, HIGH: 0 }
  );
}

async function getClaimsOverTime(days = 30) {
  const since = new Date();
  since.setDate(since.getDate() - days);

  const { data, error } = await supabaseAdmin
    .from("claims")
    .select("claim_date")
    .gte("claim_date", since.toISOString().slice(0, 10));

  if (error || !data) return [];

  const counts = new Map();
  for (const row of data) {
    const day = row.claim_date.slice(0, 10);
    counts.set(day, (counts.get(day) || 0) + 1);
  }

  return Array.from(counts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }));
}

module.exports = { getDashboardStats, getRiskDistribution, getClaimsOverTime };
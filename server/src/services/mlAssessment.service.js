/**
 * Python AI service is stateless - its computes a result and returns it but never saves it
 * saving will happen here in node, right after the AI call success
 */

const { supabaseAdmin } = require("../database/supabase");
const { logger } = require("../utils/logger");


async function persistAnalysisResult(claimId, ai) {
  const { error: assessmentError } = await supabaseAdmin.from("ml_assessments").insert({
    claim_id: claimId,
    model_version: ai.model_version || "unknown",
    risk_probability: ai.risk_probability || 0,
    risk_level: ai.risk_level || "UNKNOWN",
    features_json: ai,
  });
  if (assessmentError) {
    logger.error("ai-persist", `Failed to save ml_assessments for ${claimId}: ${assessmentError.message}`);
  }

  const signalRows = [];

  for (const rule of ai.rule_results || []) {
    if (rule.status !== "PASS") {
      signalRows.push({
        claim_id: claimId,
        signal_type: rule.rule,
        severity: rule.severity,
        description: rule.message,
        source: "RULES_ENGINE",
      });
    }
  }

  if (ai.risk_level === "HIGH" || ai.risk_level === "MEDIUM") {
    signalRows.push({
      claim_id: claimId,
      signal_type: "ELEVATED_RISK_SCORE",
      severity: ai.risk_level === "HIGH" ? "HIGH" : "MEDIUM",
      description: `Model-generated investigation probability: ${Math.round(
        (ai.risk_probability || 0) * 100
      )}%.`,
      source: "ML_MODEL",
    });
  }

  const shopHistory = ai.relationships?.repair_shop;
  if (shopHistory?.total_claims > 0 && shopHistory?.investigated_claims > 0) {
    signalRows.push({
      claim_id: claimId,
      signal_type: "REPAIR_SHOP_HISTORY",
      severity: "MEDIUM",
      description: `This repair shop has ${shopHistory.total_claims} historical claims, ${shopHistory.investigated_claims} previously investigated.`,
      source: "RELATIONSHIP_ANALYSIS",
    });
  }

  if (signalRows.length > 0) {
    const { error: signalsError } = await supabaseAdmin.from("risk_signals").insert(signalRows);
    if (signalsError) {
      logger.error("ai-persist", `Failed to save risk_signals for ${claimId}: ${signalsError.message}`);
    }
  }

  return { savedSignals: signalRows.length };
}

/**
 * Creates an investigation record the first time a claim comes back
 * flagged, or returns the existing open one.
 */
async function ensureInvestigationForFlaggedClaim(claimId, ai) {
  if (ai.risk_level !== "HIGH" && ai.risk_level !== "MEDIUM") return null;

  const { data: existing } = await supabaseAdmin
    .from("investigations")
    .select("investigation_id")
    .eq("claim_id", claimId)
    .in("status", ["OPEN", "IN_PROGRESS"])
    .maybeSingle();

  if (existing) return existing;

  const failedRules = (ai.rule_results || []).filter((r) => r.status !== "PASS").map((r) => r.message);
  const reason =
    failedRules.length > 0
      ? failedRules.join("; ")
      : `Model-generated risk level: ${ai.risk_level} (${Math.round((ai.risk_probability || 0) * 100)}%).`;

  const { data, error } = await supabaseAdmin
    .from("investigations")
    .insert({
      investigation_id: `INV-${claimId}-${Date.now()}`,
      claim_id: claimId,
      status: "OPEN",
      priority: ai.risk_level === "HIGH" ? "HIGH" : "MEDIUM",
      reason,
    })
    .select()
    .single();

  if (error) {
    logger.error("ai-persist", `Failed to create investigation for ${claimId}: ${error.message}`);
    return null;
  }
  return data;
}

module.exports = { persistAnalysisResult, ensureInvestigationForFlaggedClaim };
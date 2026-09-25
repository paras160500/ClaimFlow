const { supabaseAdmin, supabaseAuthClient } = require("../database/supabase");
const { writeAuditLog } = require("../services/audit.service");
const { AppError } = require("../utils/AppError");
const { asyncHandler } = require("../utils/asyncHandler");
const claimService = require("../services/claim.service")
const aiService = require("../services/ai.service")
const mlAssessmentService = require("../services/mlAssessment.service")
const investigationService = require("../services/inverstigation.service")
const {logger} = require("../utils/logger")

const listClaims = asyncHandler(async(req , res) => {
    const result = await claimService.listClaims(req.query)
    res.json(result)
})

const getClaim = asyncHandler(async(req , res) => {
    const claim = await claimService.getClaimById(req.params.claimId)
    await writeAuditLog({
        employeeId : req.employee.id,
        claimId : claim.claim_id,
        action : "VIEWED_CLAIM"
    })
    res.json({claim})
})

const createClaim = asyncHandler(async(req , res) => {
    const claim = await claimService.createClaim(req.body)
    await writeAuditLog({
        employeeId : req.employee.id,
        claimId : claim.claim_id ,
        action : "CREATED_CLAIM"
    })
    res.status(201).json({claim})
})


/**
 * POST /api/claims/:claimId/analyze
 * 
 * The single most important route in the Stage 3.
 * 1. It confirms the claim exists in supabase
 * 2. Calls the AI service for full investigation bundle
 * 3. Saves the result (ml_assessments, risk_signals and if the claim is risky enough open an investigation)
 * 4. Writes an audit log entry either way.
 * 5. Returns the AI result to the caller.
 */

const alayzeClaim = asyncHandler(async(req , res) => {
    const claim = await claimService.getClaimById(req.params.claimId)
    await writeAuditLog({
        employeeId : req.employee.id,
        claimId : claim.claim_id,
        action : "STARTED_AI_INVESTIGATION"
    })
    try{
        const ai = await aiService.analyzeClaim(claim.claim_id)
        await mlAssessmentService.persistAnalysisResult(claim.claim_id , ai)
        const investigation = await mlAssessmentService.ensureInvestigationForFlaggedClaim(claim.claim_id , ai)

        await writeAuditLog({
            employeeId: req.employee.id,
            claimId: claim.claim_id,
            action: "AI_INVESTIGATION_COMPLETED",
            details: `risk_level=${ai.risk_level} risk_probability=${ai.risk_probability}`,
        });
        res.json({ claim, ai, investigation });
    }
    catch (err) {
        logger.error("claims", `AI analysis failed for ${claim.claim_id}: ${err.message}`);

        await writeAuditLog({
            employeeId: req.employee.id,
            claimId: claim.claim_id,
            action: "AI_INVESTIGATION_FAILED",
            details: err.message,
        });

        // Degrade gracefully: the claim record is still fully usable even
        // though the AI commentary couldn't be generated right now.
        res.json({
            claim,
            ai: null,
            ai_error: "AI investigation summary is temporarily unavailable. The claim data is still available.",
        });
    }
})

// GET /api/claims/:claimId/history --  past investigation tied to this claim
const getClaimHistory = asyncHandler(async(req , res) => {
    const investigations = await investigationService.getInvestigationByClaim(req.params.claimId)
    res.json({ investigations })
})

/**
 * GET /api/claims/:claimId/evidence and /relationships both read from the
 * most recent stored ml_assessments row instead of re0calling the AI service.
 * the full ai response was saved into features_json at analyze time, so re-reading
 * it here is instant and doesnot rerun the llm and save cost....
 */

async function getLatestAssessment(claimId) {
  const { data } = await supabaseAdmin
    .from("ml_assessments")
    .select("features_json, created_at")
    .eq("claim_id", claimId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  return data?.features_json || null;
}

const getClaimEvidence = asyncHandler(async (req, res) => {
  const stored = await getLatestAssessment(req.params.claimId);
  res.json({
    retrieved_policy_evidence: stored?.retrieved_policy_evidence || [],
    retrieved_investigator_notes: stored?.retrieved_investigator_notes || [],
    stale: stored === null,
  });
});

const getClaimRelationships = asyncHandler(async (req, res) => {
  const stored = await getLatestAssessment(req.params.claimId);
  res.json({ relationships: stored?.relationships || null, stale: stored === null });
});

module.exports = { listClaims , getClaim , createClaim , alayzeClaim , getClaimHistory , getClaimEvidence , getClaimRelationships }
const { asyncHandler } = require("../utils/asyncHandler");
const investigationService = require("../services/inverstigation.service")
const { writeAuditLog } = require("../services/audit.service")

const listInvestigations = asyncHandler(async(req , res) => {
    const result = await investigationService.listInvestigations(req.query)
    res.json(result)
})

/**
 * POST /api/investigations/:id/decision
 * 
 * This is human-in-loop moment describe throughout the whole
 * project an investigator looks at everything the AI put together
 * and makes the actual call. Notice this route only accepts one of the 
 * four fixed decision
 */

const recordDecision = asyncHandler(async (req, res) => {
  const { decision, note } = req.body;
  const investigation = await investigationService.recordDecision(
    req.params.id,
    req.employee.email,
    decision,
    note
  );

  await writeAuditLog({
    employeeId: req.employee.id,
    claimId: investigation.claim_id,
    action: "RECORDED_DECISION",
    details: `decision=${decision}${note ? ` note="${note}"` : ""}`,
  });

  res.json({ investigation });
});

module.exports = { listInvestigations, recordDecision };
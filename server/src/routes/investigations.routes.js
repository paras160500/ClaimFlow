const { Router } = require("express");
const { requireAuth } = require("../middleware/auth");
const { requireRole } = require("../middleware/rbac");
const { validate } = require("../middleware/validate");
const { decisionSchema, investigationQuerySchema } = require("../validation/schemas");
const investigationsController = require("../controllers/investigations.controller");

const router = Router();

router.use(requireAuth);

router.get("/", validate(investigationQuerySchema, "query"), investigationsController.listInvestigations);

// Only investigators and admins record decisions -- reviewers can see
// everything (route above) but the project spec has REVIEWER "review"
// decisions, not make the original call.
router.post(
  "/:id/decision",
  requireRole("ADMIN", "INVESTIGATOR"),
  validate(decisionSchema),
  investigationsController.recordDecision
);

module.exports = router;
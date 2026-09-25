const { Router } = require("express");
const { requireAuth } = require("../middleware/auth");
const { requireRole } = require("../middleware/rbac");
const { validate } = require("../middleware/validate");
const { claimQuerySchema, createClaimSchema } = require("../validation/schemas");
const claimsController = require("../controllers/claims.controller");

const router = Router();

// Every claims route requires a logged-in employee. Read access is open to
// all three roles (Admin/Investigator/Reviewer all need to see claims);
// only the two "do something" actions below are role-restricted.
router.use(requireAuth);

router.get("/", validate(claimQuerySchema, "query"), claimsController.listClaims);
router.get("/:claimId", claimsController.getClaim);
router.get("/:claimId/history", claimsController.getClaimHistory);
router.get("/:claimId/evidence", claimsController.getClaimEvidence);
router.get("/:claimId/relationships", claimsController.getClaimRelationships);

router.post(
  "/",
  requireRole("ADMIN", "INVESTIGATOR"),
  validate(createClaimSchema),
  claimsController.createClaim
);

router.post("/:claimId/analyze", requireRole("ADMIN", "INVESTIGATOR"), claimsController.analyzeClaim);

module.exports = router;
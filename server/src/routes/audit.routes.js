const { Router } = require("express");
const { requireAuth } = require("../middleware/auth");
const { requireRole } = require("../middleware/rbac");
const auditController = require("../controllers/audit.controller");

const router = Router();

// Admin-only: audit logs exist to answer "who did what, and when" -- an
// Investigator being able to browse (and potentially notice gaps in) the
// audit trail defeats its purpose.
router.use(requireAuth, requireRole("ADMIN"));

router.get("/", auditController.getAuditLogs);

module.exports = router;
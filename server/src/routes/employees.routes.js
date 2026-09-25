const { Router } = require("express");
const { requireAuth } = require("../middleware/auth");
const { requireRole } = require("../middleware/rbac");
const { validate } = require("../middleware/validate");
const { createEmployeeSchema } = require("../validation/schemas");
const employeesController = require("../controllers/employees.controller");

const router = Router();

// The whole file is Admin-only -- managing who has accounts and what role
// they hold is exactly the kind of action that should never be reachable
// by an Investigator or Reviewer token, even by mistake.
router.use(requireAuth, requireRole("ADMIN"));

router.get("/", employeesController.listEmployees);
router.post("/", validate(createEmployeeSchema), employeesController.createEmployee);

module.exports = router;
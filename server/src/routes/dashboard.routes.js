const { Router } = require("express");
const { requireAuth } = require("../middleware/auth");
const analyticsController = require("../controllers/analytics.controller");

const router = Router();

router.get("/", requireAuth, analyticsController.getDashboard);

module.exports = router;
const { Router } = require("express");
const { requireAuth } = require("../middleware/auth");
const analyticsController = require("../controllers/analytics.controller");

const router = Router();

router.use(requireAuth);

router.get("/", analyticsController.getAnalytics);

module.exports = router;
const { Router } = require("express");
const { login, me } = require("../controllers/auth.controller");
const { requireAuth } = require("../middleware/auth");
const { validate } = require("../middleware/validate");
const { loginSchema } = require("../validation/schemas");

const router = Router();

router.post("/login", validate(loginSchema), login);
router.get("/me", requireAuth, me);

module.exports = router;
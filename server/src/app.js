const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const morgan = require("morgan");
const { env } = require("./config/env");
const { errorHandler, notFoundHandler } = require("./middleware/errorHandler");
const authRoutes = require("./routes/auth.routes");
const claimsRoutes = require("./routes/claims.routes");
const investigationsRoutes = require("./routes/investigations.routes");
const employeesRoutes = require("./routes/employees.routes");
const analyticsRoutes = require("./routes/analytics.routes");
const auditRoutes = require("./routes/audit.routes");
const dashboardRoutes = require("./routes/dashboard.routes");
const { checkAiServiceHealth } = require("./services/ai.service");

function createApp() {
  const app = express();

  // helmet sets a handful of security-related HTTP headers by default
  // (no cache leaking, no MIME sniffing, etc.) -- cheap, standard hardening
  // for any API that will eventually sit on the public internet.
  app.use(helmet());
  app.use(cors({ origin: env.allowedOrigins, credentials: true }));
  app.use(express.json());
  app.use(morgan(env.logLevel));

  app.get("/", (req, res) => {
    res.json({ service: "ClaimFlow API", stage: 3, status: "ok" });
  });

  app.get("/health", async (req, res) => {
    const aiHealthy = await checkAiServiceHealth();
    res.json({
      status: "healthy",
      ai_service: aiHealthy ? "reachable" : "unreachable",
    });
  });

  app.use("/api/auth", authRoutes);
  app.use("/api/claims", claimsRoutes);
  app.use("/api/investigations", investigationsRoutes);
  app.use("/api/employees", employeesRoutes);
  app.use("/api/analytics", analyticsRoutes);
  app.use("/api/audit-logs", auditRoutes);
  app.use("/api/dashboard", dashboardRoutes);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
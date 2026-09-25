const { createApp } = require("./app");
const { env } = require("./config/env");
const { logger } = require("./utils/logger");

const app = createApp();

app.listen(env.port, () => {
  logger.info("server", `ClaimFlow API listening on port ${env.port} (${env.nodeEnv})`);
  logger.info("server", `AI service configured at ${env.aiServiceUrl}`);
});
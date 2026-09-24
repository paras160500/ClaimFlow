/**
 * Not a real logging library but every log line with enough context
 */

const logger = {
  info: (scope, message, meta) => {
    console.log(`[${new Date().toISOString()}] [INFO] [${scope}] ${message}`, meta || "");
  },
  warn: (scope, message, meta) => {
    console.warn(`[${new Date().toISOString()}] [WARN] [${scope}] ${message}`, meta || "");
  },
  error: (scope, message, meta) => {
    console.error(`[${new Date().toISOString()}] [ERROR] [${scope}] ${message}`, meta || "");
  },
};

module.exports = { logger };
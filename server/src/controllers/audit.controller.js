const { asyncHandler } = require("../utils/asyncHandler");
const { listAuditLogs } = require("../services/audit.service");

const getAuditLogs = asyncHandler(async (req, res) => {
  const { claimId, employeeId, page, pageSize } = req.query;
  const result = await listAuditLogs({
    claimId,
    employeeId,
    page: page ? parseInt(page, 10) : 1,
    pageSize: pageSize ? parseInt(pageSize, 10) : 25,
  });
  res.json(result);
});

module.exports = { getAuditLogs };
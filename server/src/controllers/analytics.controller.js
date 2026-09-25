const { asyncHandler } = require("../utils/asyncHandler");
const analyticsService = require("../services/analytics.service")

const getDashboard = asyncHandler(async(req , res) => {
    const stats = await analyticsService.getDashboardStats()
    res.json(stats)
})


const getAnalytics = asyncHandler(async (req, res) => {
  const days = req.query.days ? parseInt(req.query.days, 10) : 30;
  const [riskDistribution, claimsOverTime] = await Promise.all([
    analyticsService.getRiskDistribution(),
    analyticsService.getClaimsOverTime(days),
  ]);
  res.json({ risk_distribution: riskDistribution, claims_over_time: claimsOverTime });
});


module.exports = { getDashboard, getAnalytics };
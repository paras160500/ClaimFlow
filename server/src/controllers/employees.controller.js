const { asyncHandler } = require("../utils/asyncHandler");
const employeeService = require("../services/employee.service");
const { writeAuditLog } = require("../services/audit.service");

const listEmployees = asyncHandler(async (req, res) => {
  const employees = await employeeService.listEmployees();
  res.json({ employees });
});

const createEmployee = asyncHandler(async (req, res) => {
  const employee = await employeeService.createEmployee(req.body);

  await writeAuditLog({
    employeeId: req.employee.id,
    action: "CREATED_EMPLOYEE",
    details: `created ${employee.email} with role ${employee.role}`,
  });

  res.status(201).json({ employee });
});

module.exports = { listEmployees, createEmployee };
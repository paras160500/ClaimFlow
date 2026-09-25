/**
 * For validation of request inorder to manage what data is going through the request
 */

const { z } = require("zod")

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

const createEmployeeSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(8),
  role: z.enum(["ADMIN", "INVESTIGATOR", "REVIEWER"]),
  department: z.string().optional(),
});

const claimQuerySchema = z.object({
  status: z.string().optional(),
  investigationStatus: z.string().optional(),
  claimType: z.string().optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
});

const createClaimSchema = z.object({
  claim_id: z.string().min(1),
  policy_id: z.string().min(1),
  customer_id: z.string().min(1),
  vehicle_id: z.string().min(1),
  repair_shop_id: z.string().optional(),
  claim_date: z.string(),
  incident_date: z.string(),
  claim_type: z.enum(["ACCIDENT", "THEFT", "FIRE", "NATURAL_DISASTER", "VANDALISM"]),
  claim_amount: z.coerce.number().positive(),
  description: z.string().optional(),
});

const decisionSchema = z.object({
  decision: z.enum(["APPROVE", "REQUEST_DOCUMENTS", "INVESTIGATE_FURTHER", "REJECT"]),
  note: z.string().optional(),
});

const investigationQuerySchema = z.object({
  status: z.string().optional(),
  priority: z.string().optional(),
  assignedTo: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
});

module.exports = {
  loginSchema,
  createEmployeeSchema,
  claimQuerySchema,
  createClaimSchema,
  decisionSchema,
  investigationQuerySchema,
};
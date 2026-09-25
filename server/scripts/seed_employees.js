/**
 * Create three demo employee accounts, one per role so we can login
 * test RBAC immedieatly without building the admin UI first 
 * 
 * npm run seed:employees
 * 
 * will print credentials for us to remember
 */

require("dotenv").config();
const { supabaseAdmin } = require("../src/database/supabase");
const { createEmployee } = require("../src/services/employee.service");

const DEMO_EMPLOYEES = [
  { name: "Ava Admin", email: "admin@claimflow.demo", password: "ClaimFlow!Admin1", role: "ADMIN", department: "Operations" },
  { name: "Ian Investigator", email: "investigator@claimflow.demo", password: "ClaimFlow!Invest1", role: "INVESTIGATOR", department: "Claims Investigation" },
  { name: "Rita Reviewer", email: "reviewer@claimflow.demo", password: "ClaimFlow!Review1", role: "REVIEWER", department: "Quality Review" },
];

async function main() {
  for (const demo of DEMO_EMPLOYEES) {
    const { data: existing } = await supabaseAdmin
      .from("employees")
      .select("id")
      .eq("email", demo.email)
      .maybeSingle();

    if (existing) {
      console.log(`  skip (already exists): ${demo.email}`);
      continue;
    }

    await createEmployee(demo);
    console.log(`  created: ${demo.email} / ${demo.password}  [${demo.role}]`);
  }
  console.log("\nDone. Log in with POST /api/auth/login using any of the accounts above.");
}

main().catch((err) => {
  console.error("Failed to seed employees:", err);
  process.exit(1);
});
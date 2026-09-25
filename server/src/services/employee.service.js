const { supabaseAdmin } = require("../database/supabase");
const { AppError } = require("../utils/AppError");

async function listEmployees() {
  const { data, error } = await supabaseAdmin
    .from("employees")
    .select("id, name, email, role, department, created_at")
    .order("created_at", { ascending: false });

  if (error) throw new AppError(`Failed to list employees: ${error.message}`, 500);
  return data || [];
}


/**
 * Employees are never self-registered (this is an internal tool -- see the
 * project's "no public customer registration" rule). An Admin creates them
 * here, which does two things in order:
 *   1. Creates a real Supabase Auth user (so they get a working login).
 *   2. Inserts the matching `employees` row with their role/department.
 * If step 2 fails, we clean up step 1 so we don't leave an orphaned auth
 * user with no employee profile.
 */

async function createEmployee(params) {
  const { data: authUser, error: authError } = await supabaseAdmin.auth.admin.createUser({
    email: params.email,
    password: params.password,
    email_confirm: true,
  });

  if (authError || !authUser?.user) {
    throw new AppError(`Failed to create login for employee: ${authError?.message}`, 400);
  }

  const { data: employee, error: employeeError } = await supabaseAdmin
    .from("employees")
    .insert({
      auth_user_id: authUser.user.id,
      name: params.name,
      email: params.email,
      role: params.role,
      department: params.department || null,
    })
    .select()
    .single();

  if (employeeError) {
    await supabaseAdmin.auth.admin.deleteUser(authUser.user.id);
    throw new AppError(`Failed to create employee profile: ${employeeError.message}`, 400);
  }

  return employee;
}

module.exports = { listEmployees, createEmployee };
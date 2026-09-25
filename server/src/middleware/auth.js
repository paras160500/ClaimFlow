/**
 * Requires a valid authorization : Bearer <token> header where <token> is
 * the access token Supabase Auth returned at login
 * 
 * Two steps:
 * - Ask supabase "is this token read, and who does it belong to?"
 *   this is the ANON clients job , it just validate the JWT
 * - Look up the matching row in our own 'employees' table to get the employees
 *   role/department- Supabase auth only knows about login credentials not our app's own employee/role model.
 * 
 * On successfull execution it will setup the req.employee and used by each downstream route
 */

const { supabaseAdmin, supabaseAuthClient } = require("../database/supabase");
const { AppError } = require("../utils/AppError");

async function requireAuth(req, res, next) {
    try {
        const header = req.headers.authorization;

        if (!header || !header.startsWith("Bearer ")) {
            throw new AppError(
                "Invalid or expired session, please log in again.",
                401
            );
        }

        const token = header.slice("Bearer ".length);

        // Validate Supabase access token
        const { data: userData, error } =
            await supabaseAuthClient.auth.getUser(token);

        if (error || !userData?.user) {
            throw new AppError(
                "Invalid or expired session, please log in again.",
                401
            );
        }

        // Find the corresponding employee
        const { data: employee, error: employeeError } =
            await supabaseAdmin
                .from("employees")
                .select("*")
                .eq("auth_user_id", userData.user.id)
                .single();

        if (employeeError || !employee) {
            throw new AppError(
                "No employee profile is linked to this account. Contact administrator.",
                403
            );
        }

        // Make employee available to controllers
        req.employee = employee;

        next();

    } catch (err) {
        next(err);
    }
}

module.exports = { requireAuth };

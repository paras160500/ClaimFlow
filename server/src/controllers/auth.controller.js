/**
 * POST /api/auth/login
 * 
 * The raect frontend never talks to supabase directly for login
 * it calls this route with email and password and this will
 * communicate with the supabase and authorize 
 */

const { supabaseAdmin, supabaseAuthClient } = require("../database/supabase");
const { writeAuditLog } = require("../services/audit.service");
const { AppError } = require("../utils/AppError");
const { asyncHandler } = require("../utils/asyncHandler");

const login = asyncHandler(async(req , res) => {
    const { email , password} = req.body 

    const { data , error } = await supabaseAuthClient.auth.signInWithPassword({ email , password })
    if(error || !data.session || !data.user) {
        throw new AppError("Invalid email or password" , 401)
    }

    const { employeeData , empError } = await supabaseAdmin
        .from("employees")
        .select("id, name, email, role, department")
        .eq("auth_user_id", data.user.id)
        .maybeSingle();

    if(!employeeData || empError) {
        throw new AppError("No employee profile is linked to this account. Contact administrator." , 403)
    }
    
    await writeAuditLog({ employeeId : employeeData.id , action : "LOGIN"})

    res.json({
        access_token : data.session.access_token,
        expires_at : data.session.expires_at
    })    
})


// GET /api/auth/me -- returns whichever employee requireAuth already resolved.

const me = asyncHandler(async(req , res) => {
    res.json({employee : req.employee})
})

module.exports = { login , me }
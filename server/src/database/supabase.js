const { createClient } = require("@supabase/supabase-js")
const { env } = require("../config/env")

/**
 * Two seprate Supabase clients, usedfor two very different purpose.
 
    - SupabaseAuthClient : uses the ANON key( the same key that is safe to put in browser) use exactly for verifying
                           a login token is real or not
    
    - SupabaseAdmin : uses SERVICE ROLE key -> a much powerfull key thhat BYPASS Row level security entirely. Every
                      actual database read/write this backend does goes through this client. This is safe because by
                      the time any code calls supabaseAdmin the reqireAuth and requireRole middleware have already
                      check the request is allowed to be here. the serice role key never leaves the server
 */


const supabaseAuthClient = createClient(env.supabaseUrl , env.supabaseAnonKey , {
    auth : {autoRefreshToken : false , persistSession : false}
})

const supabaseAdmin = createClient(env.supabaseUrl , env.supabaseServiceRoleKey , {
    auth : {autoRefreshToken : false , persistSession : false}
})

module.exports = { supabaseAuthClient , supabaseAdmin }
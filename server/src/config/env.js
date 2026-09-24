const dotenv = require("dotenv")
dotenv.config()


/**
    Reads every environment variable that app needs once at startup and 
    crashes immedieatly with a clear message if something went wrong 

    Every other file will import this env from here instead of loading
    from the process.env.PORT like that
*/

function required(name) {
    const value = process.env[name]
    if(!value){
        throw new Error(
            `Missing required environment variable : ${name}`
        )
    }
    return value 
}

function optional(name , fallback) {
    return process.env[name] || fallback
}

const env = {
    nodeEnv : optional("NODE_ENV" , "development"),
    port : parseInt(optional("PORT" , "4000") , 10),

    supabaseUrl : required("SUPABASE_URL"),
    supabaseAnonKey : required("SUPABASE_ANON_KEY"),
    supabaseServiceRoleKey : required("SUPABASE_SERVICE_ROLE_KEY"),

    aiServiceUrl : optional("AI_SERVICE_URL" , "http://localhost:8000"),
    aiServiceTimeoutMs : parseInt(optional("AI_SERVICE_TIMEOUT_MS" , "20000") , 10),

    allowedOrigins : optional("ALLOWED_ORIGINS" , "*").split(", ").map((s) => s.trim()),
    logLevel : optional("LOG_LEVEL" , "dev")
}

module.exports = { env }
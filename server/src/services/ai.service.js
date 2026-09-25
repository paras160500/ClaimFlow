/**
 * Only file in this backend that talks to the python AI serice.
 * Everything else calls the functions below instead of 
 * reaching for axios directly. So anything like AI Service URL, auth or response
 * shape change we have to update here.
 */

const  axios  = require("axios")
const { env } = require("../config/env")
const { logger } = require("../utils/logger")

const aiClient = axios.create({
    baseURL : env.aiServiceUrl,
    timeout : env.aiServiceTimeoutMs,
    headers : {"Content-Type" : "application/json"}
})

async function predictRisk(payload) {
    const { data } = await aiClient.post("/api/predict" , payload)
    return data 
}

// For calling the ml Pipeline 
async function analyzeClaim(claimId) {
    try{
        const { data } = await aiClient.post("/api/analyze-claim" , { claim_id : claimId })
        return data 
    }
    catch(err){
        const detail = err?.response?.data?.detail ?? err.message 
        logger.error("ai-service" , `analyze-claim failes for ${claimId} : ${detail}`)
        throw new Error(`AI Service Error : ${detail}`)
    }
}


async function checkAIServiceHealth() {
    try{
        const {data} = await aiClient.get("/health" , {timeout : 5000})
        return data?.status === "healthy" || data?.status === "degraded"
    }
    catch {
        return false 
    }
}

module.exports = { predictRisk , analyzeClaim , checkAIServiceHealth }
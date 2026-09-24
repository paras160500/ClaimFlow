/**
 * Each error in the app whether thrown deliberately or an unexpected bug
 * ends up here because async route is wrapped with asyncHandler() which forwards
 * errors via next(err) This is the one place that decide what the client actually sees
 */

const { AppError } = require("../utils/AppError")

function errorHandler(err , req , res ,next) {
    if(err instanceof AppError){
        return res.status(err.statusCode).json({error : err.message})
    }
    const message = err instanceof Error ? err.message  :"Unknown Error"
    console.error(`[Unhandled error] ${req.method} ${req.path} :: ` , err)

    return res.status(500).json({
        error : "Internal server error.",
        detail : process.env.NODE_ENV === "production" ? undefined : message
    })
}

function notFoundHandler(req , res) {
    res.status(404).json({
        error : `No route : ${req.method} ${req.path}`
    })
}

module.exports = { errorHandler , notFoundHandler }
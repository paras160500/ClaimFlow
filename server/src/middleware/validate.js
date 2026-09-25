/**
 * Usage : router.post("/claims" , validate(createClaimSchema , "body") , handler)
 * 
 * Runs the schema agains the req.body and on success replace req.body/req.query with the parsed
 * type-coerced result (so `?page=2` really is the number 2 by the time controller sees it. not string "2")
 */

const { ZodError } = require("zod")
const { AppError } = require("../utils/AppError")

function validate(schema , source = "body"){
    return function(req, res, next) {
        try{
            const parsed = schema.parse(req[source])
            req[source] = parsed
            next()
        }
        catch(err) {
            if(err instanceof ZodError){
                const message = err.errors.map((e) => `${e.path.join(".")} : ${e.message}`).join("; ")
                return next(new AppError(`Invalid request : ${message}` , 400))
            }
        }
    }
}

module.exports = { validate }
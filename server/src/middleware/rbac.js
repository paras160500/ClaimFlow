/**
 * router.post("/employees" , requireAuth , requireRole("ADMIN") , handler)
 * Must run after requireAuth middleware.
 */

const { AppError } = require("../utils/AppError")

function requireRole(...allowedRoles) {
    return (req , res , next) => {
        if(!req.employee) {
            return next(new AppError("Authentication is required before role checks can run." , 401))
        }
        if(!allowedRoles.includes(req.employee.role)){
            return next(
                new AppError("This action requires one of these roles : " , allowedRoles.join(", ") , 403)
            )
        }
        next()
    }
}

module.exports = { requireRole }
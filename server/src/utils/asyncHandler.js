/**
 * Express doesnot automaticall catch rejected promises from async route handlers
 * without this a thrown error inside async(Req , res) -> {} would crash the process
 * instead of being handled gracefully. wrapping every async handler with this
 * forwards any error to errorHandler.js instead
 */

const {dotenv} = require("dotenv")

function asyncHandler(fn) {
    return (req , res , next) => {
        fn(req , res , next).catch(next);
    };
}

module.exports = {asyncHandler}
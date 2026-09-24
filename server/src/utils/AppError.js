// For each error that will throw by the system will use this as it will give us
// status code and error and if nothing is pass then it will take that as 500
// unexpected error


class AppError extends Error {
    constructor(message , statusCode = 400) {
        super(message)
        this.statusCode = statusCode
        this.name = "AppError"
    }
}

module.exports = { AppError }
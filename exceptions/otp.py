from exceptions.base import BaseAppException


class InvalidOTPException(BaseAppException):
    """Exception class for invalid OTP code."""
    status_code = 400
    error_code = 30000
    detail = "The OTP service does not work."


class WrongOTPException(BaseAppException):
    status_code = 401
    error_code = 30001
    detail = "Entered code is wrong"


class NotFoundOTPException(BaseAppException):
    """Exception class for OTP code - Not Found."""
    status_code = 404
    error_code = 30002
    detail = "The OTP code - Not Found."


class SaveOTPFailedError(BaseAppException):
    """Raised when the OTP could not be saved."""
    status_code = 500
    error_code = 30003
    detail = "Failed to save OTP"


class SendOtpException(BaseAppException):
    """Raised when the OTP could not be sent."""
    status_code = 500
    error_code = 30003
    detail = "Failed to send OTP"

from exceptions.base import BaseAppException


class SendingEmailException(BaseAppException):
    """Exception class for sending email."""
    status_code = 500
    error_code = 40000
    detail = "Failed to send email"

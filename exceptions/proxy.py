from fastapi import status
from exceptions.base import BaseAppException


class CreateProxyServiceException(BaseAppException):
    status_code = 500
    error_code = 30000
    detail = "Error creating proxy (service error)"


class ModemServiceException(BaseAppException):
    status_code = 500
    error_code = 30000
    detail = "Error while connecting to modem service"

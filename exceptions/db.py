from fastapi import status
from exceptions.base import BaseAppException


class _NotFoundAppError(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "x0002"
    detail = "Данные не найдены"


class _DataError(BaseAppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "x0003"
    detail = {
        'en': 'Invalid data',
        'ru': 'Неверные данные',
        'uz': 'Noto\'g\'ri ma\'lumotlar'
    },


class _ProgrammingError(BaseAppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "x0004"
    detail = 'Ошибка SQL',


class _IntegrityError(BaseAppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "x0005"
    detail = 'Сбой целостности данных',


class _DBAPIError(BaseAppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "x0006"
    detail = 'Ошибка SQL во время исполнения запроса'

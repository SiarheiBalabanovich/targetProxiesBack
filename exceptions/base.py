from fastapi import status, HTTPException


class BaseAppException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = 'x0001'
    detail = "Возникла непредвиденная ошибка",

    def __init__(self, status_code=None, error_code=None, detail=None):
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        if detail:
            self.detail = f"{self.detail}. Error - {detail}"

        super().__init__(status_code=self.status_code, detail=self.detail)

from fastapi.requests import Request
from fastapi.exceptions import HTTPException

from typing import Optional
from jose import JWTError, jwt

from config.settings import (
    ALGORITHM_JWT,
    SECRET_KEY_JWT,
)

from crud.user import get_user_by_email


class TokenVerifier:
    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")

        if authorization is None:
            raise HTTPException(status_code=401, detail="Authentication required")

        type_auth, token = authorization.split()

        if type_auth != "Bearer":
            raise HTTPException(status_code=401, detail="Wrong type of Authentication")

        try:
            payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM_JWT])
            subject = payload.get("sub")

            if subject is None:
                raise HTTPException(status_code=403, detail="Wrong access token")
            else:
                params = dict(request.query_params) | dict(request.path_params)
                user_id = params.get('user_id')
                if user_id is not None:
                    user_id = int(user_id)

                    user = await get_user_by_email(subject)
                    if user is None:
                        raise HTTPException(status_code=404, detail="User not found")
                    if user.id != user_id and user.role.value != 'admin':
                        raise HTTPException(status_code=403, detail="Access Denied")

                return subject

        except JWTError:
            raise HTTPException(status_code=403, detail="Wrong access token")
        except HTTPException as e:
            raise e


class AdminVerifier:
    async def __call__(self, request: Request) -> Optional[bool]:
        token = TokenVerifier()

        email = await token(request)

        user = await get_user_by_email(email)

        if user.role.value == 'customer':
            raise HTTPException(status_code=403, detail="Access denied")

        return True

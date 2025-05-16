from config.settings import (
    ALGORITHM_JWT,
    SECRET_KEY_JWT,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_SAVE_SESSION_MINUTES
)
from models.user import User
from datetime import datetime, timedelta
from jose import JWTError, jwt
from logic.utils.authorization.password import PasswordManager


class JwtAuthenticator:

    def __init__(self, password: str, user: User):
        self.user = user
        self._password = password

    @staticmethod
    async def create_access_token(subject: User.email, save_session: bool = False):
        expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES if save_session is False else ACCESS_TOKEN_SAVE_SESSION_MINUTES
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        to_encode = {"exp": expire, "sub": subject}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm=ALGORITHM_JWT)
        return encoded_jwt

    @staticmethod
    async def verify_token(token):
        try:
            payload = jwt.decode(token.access_token, SECRET_KEY_JWT, algorithms=[ALGORITHM_JWT])
            subject = payload.get("sub")
            if subject is None:
                return {
                    'error': 'Invalid email or password'
                }
        except JWTError:
            return {
                'error': 'Invalid email or password'
            }
        return {
            'is_auth': True
        }

    async def authenticate(self) -> dict:
        if self._password and self.user:
            verified_pass = await PasswordManager.verify_password(self._password, self.user.password)
            if not verified_pass:
                return {
                    'error': 'Wrong Token'
                }
        elif self.user in (None, False):
            return {
                'error': 'Invalid email'
            }

        access_token = await self.create_access_token(subject=self.user.email, save_session=self.user.remember)
        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }


async def authenticate_jwt(password: str, user: User) -> dict:
    authenticator = JwtAuthenticator(password, user)
    return await authenticator.authenticate()

from urllib.parse import urlencode

from fastapi import Depends, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException

from starlette.requests import Request
from starlette import status

from authlib.integrations.starlette_client import OAuth, OAuthError
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated

from starlette.responses import JSONResponse

from config.database import get_session
from config.settings import (
    CLIENT_ID,
    CLIENT_SECRET,
    USER_DEFAULT_PASSWORD,
    FRONT_HOST,
    MAIN_HOST,
    GOOGLE_CALLBACK,
    SECRET_KEY_SESSION, GOOGLE_REDIRECT_LINK
)
from logic.authorization.google_auth import OauthService

from logic.authorization.jwt import authenticate_jwt, JwtAuthenticator
from logic.authorization.validator import TokenVerifier
from logic.stripe.customer import create_customer
from logic.authorization.otp import OTP

from scheme.custom import OAuth2PasswordRequestForm
from scheme.user import UserCreate
from scheme.token import Token

from crud.user import create_user
from crud.base import CRUDService

from models.user import User
from models.stripe import StripeAccount

router = APIRouter()

verifier = TokenVerifier()


@router.post("/token")
async def auth(
        data: Annotated[OAuth2PasswordRequestForm, Depends()],
        remember: bool = False,
        db: AsyncSession = Depends(get_session)
) -> Token:
    crud = CRUDService()

    email, password = data.email, data.password

    user = await crud.get_by_field(db, User, 'email', email, single=True)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.remember = remember

    content = await authenticate_jwt(password, user)

    if content.get('error'):
        raise HTTPException(status_code=403, detail=content.get('error'))
    await crud.update_fields(db, User, user.id, **{"remember": remember})

    token = Token(**content)

    return token


@router.get("/google-login")
async def google_login(request: Request):
    return GOOGLE_REDIRECT_LINK


@router.get(f'/google/handle')
async def google_auth(
        code: str,
        request: Request,
        db: AsyncSession = Depends(get_session)
):
    try:
        try:
            token = await OauthService().get_user_google(code)
        except OAuthError as e:
            return HTTPException(status_code=403, detail=str(e))

        crud = CRUDService()

        token_info = token.get('user')
        error = ""

        if token_info is not None:
            user = await crud.get_by_field(db, User, 'email', token_info['email'], single=True)

            if user is None:
                user_create = UserCreate(**{
                    "email": token_info['email'],
                    "first_name": token_info['given_name'],
                    "last_name": token_info['family_name'],
                    "password": USER_DEFAULT_PASSWORD
                })

                user = await create_user(db, user_create)

                stripe_user = await create_customer(f"{user.first_name} {user.last_name}", user.email)

                if not isinstance(stripe_user, dict):
                    exists = await crud.get_by_field(db, StripeAccount, 'stripe', stripe_user, single=True)
                    if exists is None:
                        await crud.create(db, StripeAccount, **{
                            "user_id": user.id,
                            "stripe": stripe_user
                        })

            access_token = await JwtAuthenticator.create_access_token(user.email, user.remember)

            quote = urlencode({"token": access_token})

        else:
            quote = urlencode({"token_error": "Error while connecting"})

        redirect_url = FRONT_HOST + "/login" + f"?" + quote

        response = RedirectResponse(redirect_url)

        response.headers["Location"] = redirect_url
        response.status_code = status.HTTP_307_TEMPORARY_REDIRECT
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/register/email/send')
async def _send_verification_email(
        email: str,
        db: AsyncSession = Depends(get_session)
):
    crud = CRUDService()

    if await crud.get_by_field(db, User, 'email', email, single=True) is not None:
        raise HTTPException(status_code=403, detail="User with this email already registered")

    service = OTP(email=email, key="regOtp")
    otp = str(await service.generate_otp())

    await service.send_otp(code=otp)
    await service.save_otp(otp)

    return JSONResponse({"status": "success", 'content': 'OTP has been sent'}, status_code=200)


@router.get('/register/email/verify')
async def _send_verification_email(
        email: str,
        otp: str,
):
    service = OTP(email=email, key="regOtp")

    await service.verify_otp(otp)

    return JSONResponse({"status": "success", 'content': 'OTP has been verified'}, status_code=200)

from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session

from logic.authorization.validator import TokenVerifier
from logic.authorization.password import RecoverPassword

from crud.user import update_user_password
from crud.base import CRUDService
from logic.utils.authorization.password import PasswordManager

from models.user import User

router = APIRouter()

verifier = TokenVerifier()


@router.post('/password/recover/sendLink')
async def send_link(email: str, db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    user = await crud.get_by_field(db, User, 'email', email, single=True)

    if user is None:
        return HTTPException(409, detail="User with this email hadn't registered")

    recover = RecoverPassword(email)

    await recover.send_recover_url()
    return JSONResponse(status_code=200, content={
        "status": "successful",
    })


@router.post('/password/recover/verifyLink')
async def verify_link(query):
    recover = RecoverPassword

    await recover.verify_user(query)

    return JSONResponse(status_code=200, content={
        "status": "successful"
    })


@router.post('/password/recover/update')
async def recover_password(query: str,
                           new_password: str,
                           confirm_password: str,
                           db: AsyncSession = Depends(get_session)
                           ):
    if new_password != confirm_password:
        raise HTTPException(status_code=422, detail="Password doesn't match")

    crud = CRUDService()
    recover = RecoverPassword

    email = await recover.verify_user(query)

    user = await crud.get_by_field(db, User, 'email', email, single=True)

    if user is None:
        raise HTTPException(status_code=500, detail="User not found")

    await update_user_password(db, user, new_password)

    return JSONResponse(status_code=200, content={
        "status": "successful",
    })


@router.post('/password/change')
async def change_password(current_password: str,
                          new_password: str,
                          confirm_password: str,
                          email: str = Depends(verifier),
                          db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    if new_password != confirm_password:
        raise HTTPException(status_code=422, detail="Password doesn't match")

    user = await crud.get_by_field(db, User, 'email', email, single=True)
    verified_pass = await PasswordManager.verify_password(current_password, user.password)

    if not verified_pass:
        raise HTTPException(status_code=403, detail="Old password is wrong")

    await update_user_password(db, user, new_password)

    return JSONResponse(status_code=200, content={
        "status": "successful",
    })


@router.post('/password/verify')
async def verify_password(password,
                          email: str = Depends(verifier),
                          db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    user = await crud.get_by_field(db, User, 'email', email, single=True)
    verified_pass = await PasswordManager.verify_password(password, user.password)

    if not verified_pass:
        raise HTTPException(status_code=403, detail="Password doesn't match")
    return JSONResponse(status_code=200, content={
        "status": "successful",
    })

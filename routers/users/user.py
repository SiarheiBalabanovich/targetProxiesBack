# import os
# import httpx
# from fastapi import Request
# from fastapi import Depends, APIRouter
# from fastapi.responses import JSONResponse
# from fastapi.exceptions import HTTPException

# from sqlalchemy.ext.asyncio import AsyncSession

# from typing import Annotated, List

# from config.database import get_session

# from logic.authorization.validator import TokenVerifier, AdminVerifier
# from logic.stripe.customer import create_customer

# from scheme.user import UserDetailInfo, UserCreate, UserDetailInfoDB, User as UserScheme, \
#     UserAllInfo as UserAllInfoScheme, UserAllInfoResponse

# from models.stripe import StripeAccount
# from models.user import UserDetailInfo as UserDetailModel, User

# from crud.user import create_user, create_user_detail, get_all_users, get_user_by_id, get_user_by_email, search_user
# from crud.base import CRUDService

# router = APIRouter()
# RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

# async def verify_recaptcha(token: str) -> bool:
#     if not RECAPTCHA_SECRET_KEY:
#         raise ValueError("RECAPTCHA_SECRET_KEY is missing")
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             "https://www.google.com/recaptcha/api/siteverify",
#             data={"secret": RECAPTCHA_SECRET_KEY, "response": token},
#         )
#         result = response.json()
#         return result.get("success", False) and result.get("score", 0) >= 0.5


# verifier = TokenVerifier()
# admin_verifier = AdminVerifier()


# @router.get('/users/detail/token')
# async def _get_user_data_by_token(email: str = Depends(verifier)) -> UserAllInfoScheme:
#     user = await get_user_by_email(email)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     detail = user.user_detail
#     if len(detail):
#         detail = detail[0]
#         detail = UserDetailInfo(
#             survey=detail.survey,
#             survey_detail=detail.survey_detail,
#             phone_number=detail.phone_number,
#             city=detail.city,
#             country=detail.country
#         )
#     else:
#         detail = None

#     return UserAllInfoScheme(
#         id=user.id,
#         first_name=user.first_name,
#         last_name=user.last_name,
#         email=user.email,
#         role=user.role.value,
#         user_detail=detail
#     )


# @router.post("/users/create")
# async def _create_user(userCreate: Annotated[UserCreate, Depends()],
#                        userDetail: Annotated[UserDetailInfo, Depends()],
#                        db: AsyncSession = Depends(get_session)):
# @router.post("/users/create")
# async def _create_user(
#     request: Request,
#     userCreate: Annotated[UserCreate, Depends()],
#     userDetail: Annotated[UserDetailInfo, Depends()],
#     db: AsyncSession = Depends(get_session)
# ):
#     recaptcha_token = request.query_params.get("recaptcha_token")

#     if not recaptcha_token or not await verify_recaptcha(recaptcha_token):
#         raise HTTPException(status_code=403, detail="Invalid captcha")
#     crud = CRUDService()

#     user = await create_user(db, userCreate)

#     if isinstance(user, dict):
#         return JSONResponse(
#             status_code=409,
#             content=user
#         )

#     user_detail = UserDetailInfoDB(
#         phone_number=userDetail.phone_number,
#         survey=userDetail.survey,
#         survey_detail=userDetail.survey_detail,
#         city=userDetail.city,
#         country=userDetail.country,
#         user_id=user.id
#     )

#     user_detail = await create_user_detail(db, user_detail)

#     stripe_user = await create_customer(f"{user.first_name} {user.last_name}", user.email)

#     if not isinstance(stripe_user, dict):
#         await crud.create(db, StripeAccount, **{
#             "user_id": user.id,
#             "stripe": stripe_user
#         })

#     return {
#         "status": "successful",
#     }


# @router.patch("/users/update/{user_id}")
# async def _update_user(user_id: int, userScheme: Annotated[UserScheme, Depends()],
#                        userDetail: Annotated[UserDetailInfo, Depends()],
#                        request_email: str = Depends(verifier),
#                        db: AsyncSession = Depends(get_session)):
#     crud = CRUDService()

#     user_data = {i: getattr(userScheme, i) for i in userScheme.model_fields_set}
#     contact_data = {i: getattr(userDetail, i) for i in userDetail.model_fields_set}

#     user_request = await crud.get_by_field(db, User, 'email', request_email, single=True)

#     if user_request.id != user_id and user_request.role.value != 'admin':
#         raise HTTPException(status_code=404, detail="Access denied")

#     user = await crud.get_by_field(db, User, 'id', user_id, single=True)

#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     user_detail = await crud.get_by_field(db, UserDetailModel, 'user_id', user_id, single=True)

#     await crud.update_fields(db, User, user_id, **user_data)

#     if user_detail is None:
#         user_detail_id = await crud.create(db, UserDetailModel, **contact_data)

#     else:
#         user_detail_id = user_detail.id
#         await crud.update_fields(db, UserDetailModel, user_detail_id, **contact_data)

#     return JSONResponse(content={
#         "status": "successful"
#     })


# @router.get("/users/list", dependencies=[Depends(admin_verifier)])
# async def get_users(offset: int = 0,
#                     limit: int = 10,
#                     db: AsyncSession = Depends(get_session)) -> UserAllInfoResponse:
#     users = await get_all_users(db)
#     result = []

#     if not len(users):
#         raise HTTPException(status_code=404, detail="Users not found")

#     for user in users[offset: offset + limit]:
#         detail = user.user_detail
#         if len(detail):
#             detail = detail[0]

#             detail = UserDetailInfo(
#                 survey=detail.survey,
#                 survey_detail=detail.survey,
#                 phone_number=detail.phone_number,
#                 city=detail.city,
#                 country=detail.country
#             )
#         else:
#             detail = None

#         result.append(
#             UserAllInfoScheme(
#                 id=user.id,
#                 first_name=user.first_name,
#                 last_name=user.last_name,
#                 email=user.email,
#                 role=user.role.value,
#                 user_detail=detail
#             )
#         )

#     return UserAllInfoResponse(
#         total=len(users),
#         users=result
#     )


# @router.get('/users/search', dependencies=[Depends(admin_verifier)])
# async def _search_user(query: str,
#                        offset: int = 0,
#                        limit: int = 10,
#                        db: AsyncSession = Depends(get_session)):
#     users = await search_user(db, query)
#     result = []
#     if not len(users):
#         raise HTTPException(status_code=404, detail="Users not found")

#     for user in users[offset: offset + limit]:
#         detail = user.user_detail
#         if len(detail):
#             detail = detail[0]

#             detail = UserDetailInfo(
#                 survey=detail.survey,
#                 survey_detail=detail.survey,
#                 phone_number=detail.phone_number,
#                 city=detail.city,
#                 country=detail.country
#             )
#         else:
#             detail = None

#         result.append(
#             UserAllInfoScheme(
#                 id=user.id,
#                 first_name=user.first_name,
#                 last_name=user.last_name,
#                 email=user.email,
#                 role=user.role.value,
#                 user_detail=detail
#             )
#         )

#     return UserAllInfoResponse(
#         total=len(users),
#         users=result
#     )


# @router.delete('/users/delete/{user_id}', dependencies=[Depends(admin_verifier)])
# async def _delete_user(user_id: int,
#                        db: AsyncSession = Depends(get_session)):
#     crud = CRUDService()

#     user = await crud.get_by_field(db, User, 'id', user_id, single=True)

#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     await crud.update_fields(db, User, user_id, **{'is_active': False})

#     return {
#         "status": "successful"
#     }


# @router.get('/users/detail/{user_id}')
# async def _get_detail_user(user_id: int,
#                            email: str = Depends(verifier),
#                            db: AsyncSession = Depends(get_session)) -> UserAllInfoScheme:
#     crud = CRUDService()
#     user_request = await crud.get_by_field(db, User, 'email', email, single=True)

#     if user_request.id != user_id and user_request.role.value != 'admin':
#         raise HTTPException(status_code=403, detail="Access denied")

#     user = await get_user_by_id(db, user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     detail = user.user_detail
#     if len(detail):
#         detail = detail[0]
#         detail = UserDetailInfo(
#             survey=detail.survey,
#             survey_detail=detail.survey_detail,
#             phone_number=detail.phone_number,
#             city=detail.city,
#             country=detail.country
#         )
#     else:
#         detail = None

#     return UserAllInfoScheme(
#         id=user.id,
#         first_name=user.first_name,
#         last_name=user.last_name,
#         email=user.email,
#         role=user.role.value,
#         user_detail=detail
#     )


import os
import httpx
from fastapi import Request, Depends, APIRouter, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated, List

from config.database import get_session
from logic.authorization.validator import TokenVerifier, AdminVerifier
from logic.stripe.customer import create_customer

from scheme.user import (
    UserDetailInfo, UserCreate, UserDetailInfoDB, User as UserScheme,
    UserAllInfo as UserAllInfoScheme, UserAllInfoResponse
)

from models.stripe import StripeAccount
from models.user import UserDetailInfo as UserDetailModel, User

from crud.user import (
    create_user, create_user_detail, get_all_users,
    get_user_by_id, get_user_by_email, search_user
)
from crud.base import CRUDService
from pydantic import BaseModel

router = APIRouter()
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

# ==== HELPER ====
async def verify_recaptcha(token: str) -> bool:
    if not RECAPTCHA_SECRET_KEY:
        raise ValueError("RECAPTCHA_SECRET_KEY is missing")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SECRET_KEY, "response": token},
        )
        result = response.json()
        return result.get("success", False) and result.get("score", 0) >= 0.5

verifier = TokenVerifier()
admin_verifier = AdminVerifier()

# ==== СХЕМА ДЛЯ JSON BODY ====
class CreateUserPayload(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    survey: str
    survey_detail: str | None = None
    phone_number: str | None = None
    city: str
    country: str
    recaptcha_token: str | None = None

# ==== РЕГИСТРАЦИЯ (ТОЛЬКО BODY, НИКАКИХ QUERY) ====
@router.post("/users/create")
async def create_user_json(
    payload: CreateUserPayload,
    db: AsyncSession = Depends(get_session)
):
    
    # if not payload.recaptcha_token or not await verify_recaptcha(payload.recaptcha_token):
    #     raise HTTPException(status_code=403, detail="Invalid captcha")

    user = await create_user(db, payload)
    if isinstance(user, dict):
        return JSONResponse(status_code=409, content=user)

    user_detail = UserDetailInfoDB(
        phone_number=payload.phone_number,
        survey=payload.survey,
        survey_detail=payload.survey_detail,
        city=payload.city,
        country=payload.country,
        user_id=user.id
    )
    user_detail = await create_user_detail(db, user_detail)

    # Stripe
    stripe_user = await create_customer(f"{payload.first_name} {payload.last_name}", payload.email)
    crud = CRUDService()
    if not isinstance(stripe_user, dict):
        await crud.create(db, StripeAccount, **{
            "user_id": user.id,
            "stripe": stripe_user
        })

    return {"status": "successful"}


@router.get('/users/detail/token')
async def _get_user_data_by_token(email: str = Depends(verifier)) -> UserAllInfoScheme:
    user = await get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    detail = user.user_detail
    if len(detail):
        detail = detail[0]
        detail = UserDetailInfo(
            survey=detail.survey,
            survey_detail=detail.survey_detail,
            phone_number=detail.phone_number,
            city=detail.city,
            country=detail.country
        )
    else:
        detail = None

    return UserAllInfoScheme(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role.value,
        user_detail=detail
    )

@router.patch("/users/update/{user_id}")
async def _update_user(user_id: int, userScheme: Annotated[UserScheme, Depends()],
                       userDetail: Annotated[UserDetailInfo, Depends()],
                       request_email: str = Depends(verifier),
                       db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    user_data = {i: getattr(userScheme, i) for i in userScheme.model_fields_set}
    contact_data = {i: getattr(userDetail, i) for i in userDetail.model_fields_set}

    user_request = await crud.get_by_field(db, User, 'email', request_email, single=True)

    if user_request.id != user_id and user_request.role.value != 'admin':
        raise HTTPException(status_code=404, detail="Access denied")

    user = await crud.get_by_field(db, User, 'id', user_id, single=True)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_detail = await crud.get_by_field(db, UserDetailModel, 'user_id', user_id, single=True)

    await crud.update_fields(db, User, user_id, **user_data)

    if user_detail is None:
        user_detail_id = await crud.create(db, UserDetailModel, **contact_data)
    else:
        user_detail_id = user_detail.id
        await crud.update_fields(db, UserDetailModel, user_detail_id, **contact_data)

    return JSONResponse(content={"status": "successful"})


@router.get("/users/list", dependencies=[Depends(admin_verifier)])
async def get_users(offset: int = 0,
                    limit: int = 10,
                    db: AsyncSession = Depends(get_session)) -> UserAllInfoResponse:
    users = await get_all_users(db)
    result = []

    if not len(users):
        raise HTTPException(status_code=404, detail="Users not found")

    for user in users[offset: offset + limit]:
        detail = user.user_detail
        if len(detail):
            detail = detail[0]
            detail = UserDetailInfo(
                survey=detail.survey,
                survey_detail=detail.survey,
                phone_number=detail.phone_number,
                city=detail.city,
                country=detail.country
            )
        else:
            detail = None

        result.append(
            UserAllInfoScheme(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                role=user.role.value,
                user_detail=detail
            )
        )

    return UserAllInfoResponse(total=len(users), users=result)


@router.get('/users/search', dependencies=[Depends(admin_verifier)])
async def _search_user(query: str,
                       offset: int = 0,
                       limit: int = 10,
                       db: AsyncSession = Depends(get_session)):
    users = await search_user(db, query)
    result = []
    if not len(users):
        raise HTTPException(status_code=404, detail="Users not found")

    for user in users[offset: offset + limit]:
        detail = user.user_detail
        if len(detail):
            detail = detail[0]
            detail = UserDetailInfo(
                survey=detail.survey,
                survey_detail=detail.survey,
                phone_number=detail.phone_number,
                city=detail.city,
                country=detail.country
            )
        else:
            detail = None

        result.append(
            UserAllInfoScheme(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                role=user.role.value,
                user_detail=detail
            )
        )

    return UserAllInfoResponse(total=len(users), users=result)


@router.delete('/users/delete/{user_id}', dependencies=[Depends(admin_verifier)])
async def _delete_user(user_id: int,
                       db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    user = await crud.get_by_field(db, User, 'id', user_id, single=True)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await crud.update_fields(db, User, user_id, **{'is_active': False})

    return {"status": "successful"}


@router.get('/users/detail/{user_id}')
async def _get_detail_user(user_id: int,
                           email: str = Depends(verifier),
                           db: AsyncSession = Depends(get_session)) -> UserAllInfoScheme:
    crud = CRUDService()
    user_request = await crud.get_by_field(db, User, 'email', email, single=True)

    if user_request.id != user_id and user_request.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    detail = user.user_detail
    if len(detail):
        detail = detail[0]
        detail = UserDetailInfo(
            survey=detail.survey,
            survey_detail=detail.survey_detail,
            phone_number=detail.phone_number,
            city=detail.city,
            country=detail.country
        )
    else:
        detail = None

    return UserAllInfoScheme(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role.value,
        user_detail=detail
    )

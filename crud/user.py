from typing import Union, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import asyncio

from sqlalchemy.orm import selectinload
from sqlalchemy.orm import defer

from config.database import async_session
from models.user import User, UserDetailInfo
from scheme.user import UserCreate, UserDetailInfoDB

from logic.utils.authorization.password import PasswordManager


async def create_user(db: AsyncSession, user: UserCreate) -> Union[User, Dict[str, str]]:
    result = await asyncio.gather(db.execute(select(User).where(User.email == user.email)))

    existing_user = result[0].scalar()
    if existing_user:
        return {'error': 'User with this email already exists'}

    hashed_password = await PasswordManager.hash_password(user.password)
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_password,
    )
    db.add(db_user)

    await db.commit()
    await db.refresh(db_user)

    return db_user


async def update_user_password(db: AsyncSession, user: User, password):
    hashed_password = await PasswordManager.hash_password(password)

    user.password = hashed_password

    await db.commit()
    await db.refresh(user)

    return user


async def create_user_detail(db: AsyncSession, user_detail: UserDetailInfoDB) -> Union[User, Dict[str, str]]:
    db_user = UserDetailInfo(
        phone_number=user_detail.phone_number,
        survey=user_detail.survey,
        survey_detail=user_detail.survey_detail,
        city=user_detail.city,
        country=user_detail.country,
        user_id=user_detail.user_id
    )

    db.add(db_user)

    await db.commit()
    await db.refresh(db_user)

    return db_user


async def get_user_by_email(email: str):
    query = (
        select(User)
        .options(
            selectinload(User.user_detail),
            defer(User.password)
        )
        .where(
            User.is_active == True,
            User.email == email
        )
    )

    async with async_session() as session:
        result = await session.execute(query)

        user = result.scalars().first()
        return user


async def get_all_users(db: AsyncSession):
    query = select(User).options(selectinload(User.user_detail), defer(User.password)).where(User.is_active == True)

    result = await db.execute(query)

    return result.scalars().all()


async def search_user(db: AsyncSession, query: str):
    _query = (
        select(User).where(
            User.first_name.ilike(f"%{query}%") |
            User.last_name.ilike(f"%{query}%") |
            User.email.ilike(f"%{query}%")
        ).options(
            selectinload(User.user_detail),
        )
    )
    result = await db.execute(_query)

    return result.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: int):
    query = (
        select(User)
        .options(
            selectinload(User.user_detail),
            defer(User.password)
        )
        .where(
            User.is_active == True,
            User.id == user_id
        )
    )

    result = await db.execute(query)

    return result.scalars().first()

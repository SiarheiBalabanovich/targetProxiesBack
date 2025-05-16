from sqlalchemy.ext.asyncio import AsyncSession
from config.database import async_session

from models.notify import Notify
from sqlalchemy import select


async def get_notifies(db: AsyncSession, user_id: int, is_read=None):

    clause = [Notify.user_id == user_id]

    if is_read is not None:
        clause.append(
            Notify.is_read == is_read
        )

    query = (
        select(
            Notify
        )
        .where(
            *clause
        )
        .order_by(
            Notify.is_read.desc(),
            Notify.date_created.desc(),
        )
    )

    result = await db.execute(query)

    return result.scalars().all()


async def create_notify(user_id: int, message: str, type: str):

    async with async_session() as db:
        instance = Notify(
                user_id=user_id,
                message=message,
                type=type
            )
        db.add(instance)

        await db.commit()
        await db.refresh(instance)

        return instance

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.pages import Page
from sqlalchemy import select, or_, func, cast, JSON


async def get_pages(db: AsyncSession):
    query = (
        select(Page)
        .options(
            selectinload(Page.user_created),
            selectinload(Page.user_updated)
        )
    )

    result = await db.execute(query)

    return result.scalars().all()


async def search_pages(db: AsyncSession, query: str):
    _query = (
        select(Page).where(
            Page.name.ilike(f"%{query}%") |
            Page.title.ilike(f"%{query}%") |
            Page.content.ilike(f"%{query}%") |
            Page.comments.ilike(f"%{query}%")
        ).options(
            selectinload(Page.user_created),
            selectinload(Page.user_updated)
        )
    )

    result = await db.execute(_query)

    return result.scalars().all()

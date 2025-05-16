from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDService
from models.discounts import Discount


async def update_discount(discount_id: int, db: AsyncSession):

    crud = CRUDService()

    discount = await crud.get_by_field(db, Discount, 'id', int(discount_id), single=True)
    if discount is not None:
        users = discount.limit_users
        if isinstance(users, int):
            await crud.update_fields(db, Discount, int(discount_id), **{'limit_users': users - 1})
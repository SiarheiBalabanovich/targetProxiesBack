import datetime
import pytz
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session

from crud.base import CRUDService

from scheme.discount import DiscountOut, DiscountUpdate, DiscountCreate
from logic.authorization.validator import AdminVerifier

from models.discounts import Discount

from typing import Annotated

admin_verifier = AdminVerifier()

router = APIRouter()

UTC = pytz.UTC


@router.get("/discount/{discount_id}", dependencies=[Depends(admin_verifier)])
async def read_discount(discount_id: int, db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    discount = await crud.get_by_field(db, Discount, 'id', discount_id, single=True)
    if discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    return discount


@router.get("/discounts", dependencies=[Depends(admin_verifier)])
async def get_discounts(db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    discounts = await crud.get_all(db, Discount)
    if not len(discounts):
        raise HTTPException(status_code=404, detail="Discounts not found")

    return discounts[::-1]


@router.post("/discount", dependencies=[Depends(admin_verifier)])
async def create_discount(discount: Annotated[DiscountCreate, Depends()],
                          db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    data = {i: getattr(discount, i) for i in discount.model_fields_set}

    discount = await crud.create(db, Discount, **data)

    return {
        "status": "successful"
    }


@router.patch("/discount/{discount_id}", dependencies=[Depends(AdminVerifier)])
async def update_discount(discount_id: int,
                          discount: Annotated[DiscountUpdate, Depends()],
                          db: AsyncSession = Depends(get_session)
                          ):
    crud = CRUDService()
    data = {i: getattr(discount, i) for i in discount.model_fields_set}

    discount = await crud.update_fields(db, Discount, discount_id, **data)
    return {
        "status": "successful"
    }


@router.delete("/discount/{discount_id}", dependencies=[Depends(AdminVerifier)])
async def delete_discount(discount_id: int,
                          db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    await crud.delete(db, Discount, discount_id)
    return {
        "status": "successful"
    }


@router.get('/discounts/apply')
async def apply_discount(code: str,
                         db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    today = UTC.localize(datetime.datetime.now())

    discount = await crud.get_by_field(db, Discount, 'code', code, single=True)

    if discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    if isinstance(discount.limit_users, int) and discount.limit_users <= 0:
        raise HTTPException(status_code=422, detail="No more activations for this discount")

    if today >= discount.expiry_date:
        raise HTTPException(status_code=403, detail="Discount has expired")

    if today <= discount.effective_date:
        raise HTTPException(status_code=403, detail="Discount not started yet")

    return discount

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from logic.authorization.validator import AdminVerifier, TokenVerifier

from crud.balance import get_all_payment_graphics
from crud.user import get_all_users
from crud.stripe import get_users_subscriptions_active, get_length_users_with_discount, get_total_users_with_sub

from scheme.stat import StatInterface

admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter()


@router.get('/adminPanel/stats', dependencies=[Depends(admin_verifier)])
async def _get_admin_stats(db: AsyncSession = Depends(get_session)) -> StatInterface:
    all_users = await get_all_users(db)
    with_sub = await get_users_subscriptions_active(db)
    users_with_discount = await get_length_users_with_discount(db)
    total_users_with_sub = await get_total_users_with_sub(db)

    return StatInterface(
        total=len(all_users),
        total_with_active_sub=with_sub,
        total_with_discount=users_with_discount,
        total_paid=total_users_with_sub
    )

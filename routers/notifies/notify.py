from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from crud.base import CRUDService
from crud.notify import get_notifies

from logic.authorization.validator import AdminVerifier, TokenVerifier

from models.notify import Notify
from models.user import User

from scheme.notifies import NotifyScheme, NotifyResponse


admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter()


@router.get('/notifies')
async def get_user_notifies(offset: int = 0,
                            limit: int = 10,
                            is_read: Optional[bool] = None,
                            email: str = Depends(verifier),
                            db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    result = []

    user = await crud.get_by_field(db, User, 'email', email, single=True)

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    notifies = await get_notifies(db, user.id, is_read)

    if not len(notifies):
        raise HTTPException(status_code=404, detail="Notifies not found")

    for notify in notifies[offset: limit + offset]:
        result.append(
            NotifyScheme(
                id=notify.id,
                user_id=notify.user_id,
                is_read=notify.is_read,
                message=notify.message,
                type=notify.type,
                date_created=notify.date_created
            )
        )

    return NotifyResponse(
        total=len(notifies),
        notifies=result.copy()
    )


@router.patch('/notifies/update')
async def _update_notify(notify_id: int,
                         email: str = Depends(verifier),
                         db: AsyncSession = Depends(get_session)):

    crud = CRUDService()

    user = await crud.get_by_field(db, User, 'email', email, single=True)

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    notify = await crud.get_one(db, Notify, notify_id)

    await crud.update_fields(db, Notify, notify.id, **{'is_read': True})

    return {
        "status": "successful"
    }


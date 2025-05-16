from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from crud.base import CRUDService
from crud.notify import create_notify
from crud.pages import get_pages, search_pages

from logic.authorization.validator import AdminVerifier, TokenVerifier

from models.pages import Page
from models.user import User

from scheme.pages import PageInterfaceResponse, PageInterface, PageCreate, PageUserScheme
from datetime import datetime

admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter()


@router.get('/pages/list')
async def _get_pages(offset: int = 0,
                     limit: int = 10,
                     db: AsyncSession = Depends(get_session)) -> PageInterfaceResponse:
    pages = await get_pages(db)
    result = []
    if not len(pages):
        raise HTTPException(status_code=404, detail="Pages not found")

    for page in pages[offset: limit + offset][::-1]:
        user_created = None if page.user_created is None else PageUserScheme(
            id=page.user_created.id,
            email=page.user_created.email,
        )
        user_updated = None if page.user_updated is None else PageUserScheme(
            id=page.user_updated.id,
            email=page.user_updated.email,
        )
        result.append(
            PageInterface(
                id=page.id,
                name=page.name,
                title=page.title,
                content=page.content,
                visibility=page.visibility.value,
                status=page.status.value,
                comments=page.comments,
                user_created=user_created,
                user_updated=user_updated,
                date_created=datetime.strftime(page.date_created, "%d/%m/%y"),
                date_updated=datetime.strftime(page.date_updated,
                                               "%d/%m/%y") if page.date_updated is not None else page.date_updated
            )
        )
    return PageInterfaceResponse(
        total=len(pages),
        pages=result
    )


@router.post('/pages/create', dependencies=[Depends(admin_verifier)])
async def create_page(page: Annotated[PageCreate, Depends()],
                      email: str = Depends(verifier),
                      db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    user = await crud.get_by_field(db, User, 'email', email, single=True)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    data = {i: getattr(page, i) for i in page.model_fields_set}
    data['user_created_id'] = user.id

    await crud.create(db, Page, **data)

    users = await crud.get_by_fields(db, User, {"is_active": True})

    for user in users:
        await create_notify(user.id, f"New page of documentation added", type="doc_create")
    return {
        "status": "successful"
    }


@router.patch('/pages/update/{page_id}', dependencies=[Depends(admin_verifier)])
async def _update_page(page_id: int,
                       page: Annotated[PageCreate, Depends()],
                       email: str = Depends(verifier),
                       db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    data = {i: getattr(page, i) for i in page.model_fields_set}

    page = await crud.get_by_field(db, Page, 'id', page_id, single=True)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    user = await crud.get_by_field(db, User, 'email', email, single=True)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    data['user_updated_id'] = user.id
    data['date_updated'] = datetime.utcnow()

    await crud.update_fields(db, Page, page_id, **data)

    users = await crud.get_by_fields(db, User, {"is_active": True})

    for user in users:
        await create_notify(user.id, f"Documentation updated", type="doc_update")

    return {
        "status": "successful"
    }


@router.delete('/pages/{page_id}', dependencies=[Depends(admin_verifier)])
async def _delete_page(page_id: int,
                       db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    page = await crud.get_by_field(db, Page, 'id', page_id, single=True)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    await crud.delete(db, Page, page_id)

    return {
        'status': "successful"
    }


@router.get('/pages/search', dependencies=[Depends(admin_verifier)])
async def _search_pages(query: str,
                        offset: int = 0,
                        limit: int = 10,
                        db: AsyncSession = Depends(get_session)):
    pages = await search_pages(db, query)
    result = []

    if not len(pages):
        raise HTTPException(status_code=404, detail="Pages not found")

    for page in pages[offset: limit + offset]:
        user_created = None if page.user_created is None else PageUserScheme(
            id=page.user_created.id,
            email=page.user_created.email,
        )
        user_updated = None if page.user_updated is None else PageUserScheme(
            id=page.user_updated.id,
            email=page.user_updated.email,
        )
        result.append(
            PageInterface(
                id=page.id,
                name=page.name,
                title=page.title,
                content=page.content,
                visibility=page.visibility.value,
                status=page.status.value,
                comments=page.comments,
                user_created=user_created,
                user_updated=user_updated,
                date_created=datetime.strftime(page.date_created, "%d/%m/%y"),
                date_updated=datetime.strftime(page.date_updated,
                                               "%d/%m/%y") if page.date_updated is not None else page.date_updated
            )
        )
    return PageInterfaceResponse(
        total=len(pages),
        pages=result
    )

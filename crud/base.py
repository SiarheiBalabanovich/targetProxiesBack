from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import IntegrityError, DataError, ProgrammingError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from exceptions.db import (
    _NotFoundAppError,
    _IntegrityError,
    _ProgrammingError,
    _DataError,
    _DBAPIError,
    BaseAppException
)


class CRUDService:

    async def create(self, session: AsyncSession, model, **kwargs):
        try:
            instance = model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance.id
        except IntegrityError as ie:
            raise _IntegrityError(detail=str(ie))
        except DataError as de:
            raise _DataError(detail=str(de))
        except ProgrammingError as pe:
            raise _ProgrammingError(detail=str(pe))
        except Exception as e:
            raise BaseAppException(detail=str(e))

    async def get_one(self, session: AsyncSession, model, id: int):
        try:
            result = await session.execute(select(model).filter_by(id=id))
            return result.scalar_one()
        except NoResultFound as e:
            raise _NotFoundAppError(detail=str(e))
        except Exception as e:
            raise BaseAppException(detail=str(e))

    async def get_all(self, session: AsyncSession, model):
        try:
            result = await session.execute(select(model))
            return result.scalars().all()
        except ProgrammingError as pe:
            raise _ProgrammingError(detail=str(pe))
        except Exception as e:
            raise BaseAppException(detail=str(e))

    async def get_by_field(self, session: AsyncSession, model, field: str, value, single=False):
        if not hasattr(model, field):
            raise ValueError(f"Model {model.__name__} does not have field {field}")
        try:
            result = await session.execute(select(model).filter(getattr(model, field) == value))
            if not single:
                return result.scalars().all()
            return result.scalars().first()
        except NoResultFound as e:
            raise _NotFoundAppError(detail=str(e))
        except DBAPIError as e:
            raise _DBAPIError(detail=str(e))
        except Exception as e:
            raise BaseAppException(detail=str(e))

    async def get_by_fields(self, session: AsyncSession, model, fields: dict, single=False):
        try:
            conditions = [getattr(model, field) == value for field, value in fields.items()]
            result = await session.execute(select(model).filter(and_(*conditions)))
            if not single:
                return result.scalars().all()
            return result.scalars().first()
        except NoResultFound as e:
            raise _NotFoundAppError(detail=str(e))
        except DBAPIError as e:
            raise _DBAPIError(detail=str(e))
        except Exception as e:
            raise BaseAppException(detail=str(e))

    async def update_fields(self, session: AsyncSession, model, id: int, **kwargs):
        try:
            instance = await self.get_one(session, model, id)
            for field, value in kwargs.items():
                setattr(instance, field, value)
            await session.commit()
            await session.refresh(instance)
            return instance
        except NoResultFound as e:
            raise _NotFoundAppError(detail=str(e))
        except IntegrityError as ie:
            raise _IntegrityError(detail=str(ie))
        except DataError as de:
            raise _DataError(detail=str(de))
        except ProgrammingError as pe:
            raise _ProgrammingError(detail=str(pe))
        except Exception as e:
            raise BaseAppException(detail=str(e))

    async def delete(self, session: AsyncSession, model, id: int):
        try:
            instance = await self.get_one(session, model, id)
            await session.delete(instance)
            await session.commit()
        except NoResultFound as e:
            raise _NotFoundAppError
        except IntegrityError as ie:
            raise _IntegrityError
        except DataError as de:
            raise _DataError
        except ProgrammingError as pe:
            raise _ProgrammingError
        except Exception as e:
            raise BaseAppException
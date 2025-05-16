import enum

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func, Enum

from models.user import User

from config.database import Base


class TypeNotify(enum.Enum):
    proxy_buy = "proxy_buy"
    proxy_prolong = "proxy_prolong"
    proxy_delete = "proxy_delete"
    doc_create = "doc_create"
    doc_update = "doc_update"


class Notify(Base):
    __tablename__ = 'notifies'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(Enum(TypeNotify, server_default='proxy_buy'))

    user_id = Column(Integer, ForeignKey(User.id))
    message = Column(String)
    is_read = Column(Boolean, default=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now())

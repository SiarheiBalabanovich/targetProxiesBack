from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import relationship

from models.user import User

from config.database import Base
import enum


class Visibility(enum.Enum):
    public = "public"
    private = "private"


class Status(enum.Enum):
    draft = "draft"
    published = "published"


class Page(Base):
    __tablename__ = 'pages'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String)
    title = Column(String)

    content = Column(String)
    comments = Column(String, nullable=True)

    user_created_id = Column(Integer, ForeignKey(User.id, ondelete='SET NULL'), nullable=True)
    user_updated_id = Column(Integer, ForeignKey(User.id, ondelete='SET NULL'), nullable=True)

    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now())

    visibility = Column(Enum(Visibility))
    status = Column(Enum(Status))

    user_created = relationship(User, uselist=False, foreign_keys=[user_created_id])
    user_updated = relationship(User, uselist=False, foreign_keys=[user_updated_id])

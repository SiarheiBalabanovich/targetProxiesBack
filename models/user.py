from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from config.database import Base

import enum


class UserRole(enum.Enum):
    customer = "customer"
    admin = "admin"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String, default=None, nullable=False)
    role = Column(Enum(UserRole), server_default="customer")
    is_active = Column(Boolean, default=True)
    remember = Column(Boolean, default=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now())

    user_detail = relationship('UserDetailInfo', back_populates="user")
    user_stripe = relationship('StripeAccount', back_populates="user")
    user_crypto = relationship('UserCryptoBalance')


class UserDetailInfo(Base):
    __tablename__ = 'users_info'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), unique=True)

    survey = Column(String)
    survey_detail = Column(String, nullable=True)

    phone_number = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)

    user = relationship(User, back_populates="user_detail")


class UserCryptoBalance(Base):
    __tablename__ = 'users_crypto_balance'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    amount = Column(Float, default=0.0)

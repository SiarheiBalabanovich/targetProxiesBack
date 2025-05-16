import enum

from sqlalchemy import Column, Integer, String, Float, Enum
from config.database import Base

from sqlalchemy.types import TIMESTAMP


class DiscountType(enum.Enum):
    fixed = "fixed"
    percent = "percent"


class Discount(Base):
    __tablename__ = 'discounts'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, unique=True)
    discount_amount = Column(Float)
    order_amount = Column(Float)
    type = Column(Enum(DiscountType), server_default='fixed')
    limit_users = Column(Integer, nullable=True)
    effective_date = Column(type_=TIMESTAMP(timezone=True))
    expiry_date = Column(type_=TIMESTAMP(timezone=True))

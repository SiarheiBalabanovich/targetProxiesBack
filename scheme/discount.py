from typing import Optional

from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class DiscountBase(BaseModel):
    code: str
    discount_amount: float
    order_amount: float
    limit_users: Optional[int] = None
    effective_date: datetime
    expiry_date: datetime
    type: Literal['fixed', 'percent']


class DiscountCreate(DiscountBase):
    pass


class DiscountUpdate(DiscountBase):
    pass


class DiscountInDB(DiscountBase):
    id: int


class DiscountOut(DiscountBase):
    id: int

from typing import List, Optional

from pydantic import BaseModel
from datetime import datetime


class PurchasesBalance(BaseModel):
    total_payment_per_month: int
    total_purchases: int
    crypto_balance: int


class ClosestPayments(BaseModel):
    subscription_id: int
    subscription_item_id: int
    carrier_name: str
    proxy_location: str
    days_left: int


class ClosestPaymentsResponse(BaseModel):
    total: int
    payments: List[ClosestPayments]


class LastPayment(BaseModel):
    subscription_id: int
    subscription_item_id: int

    date_payment: datetime
    amount: int
    is_active: bool

    order_id: Optional[int]
    http_ip: str
    http_port: int
    socks5_ip: str
    socks5_port: int
    carrier_name: str
    proxy_location: str

from pydantic import BaseModel
from typing import Optional, List, Any, Literal, Union


class SubscriptionInterface(BaseModel):
    order_id: int
    subscription_id: int
    payment_per_period: float
    payment_data: Optional[dict] = None
    period_str: Optional[str] = None
    due_date: str
    expires: int
    auto_extend: bool | int


class SubscriptionInterfaceResponse(BaseModel):
    total: int
    subscriptions: List[SubscriptionInterface]


class OrderInterface(BaseModel):
    order_id: Optional[int] = None
    first_name: str
    last_name: str
    email: str

    payment_link: Optional[str] = None

    date_created: str
    carrier: str

    amount: float

    period_str: Optional[str] = None
    discount_amount: Optional[float] = None
    discount_code: Optional[str] = None
    payment_method: Optional[Union[dict, str]] = None
    status: Literal['success', 'pending', 'failed']


class OrderInterfaceResponse(BaseModel):
    total: int
    orders: List[OrderInterface]


class SubscriptionPayment(BaseModel):
    payment_date: str
    subscription_id: int
    subscription_item_id: int
    order_id: int
    modem_name: str
    proxy_id: int
    proxy_location: str
    period_str: str
    discount: Optional[float] = None
    amount: float


class SubscriptionPaymentResponse(BaseModel):
    total: int
    payments: List[SubscriptionPayment]


class SubscriptionLast(SubscriptionPayment):
    login: str
    password: str
    order_id: Optional[int] = None
    transaction_id: Optional[int] = None
    renewal_date: Optional[str] = None
    payment_item_per_month: Optional[float] = None
    next_payment_days: Optional[float] = None
    payment_method: Optional[dict | str] = None
    date_end: Optional[str] = None

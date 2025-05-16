from pydantic import BaseModel
from typing import Optional


class GraphicInterface(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = 0.0


class GraphicExtraInterface(GraphicInterface):
    period: str


class GraphicMultiInterfaceCarrier(BaseModel):
    name: Optional[str] = None
    tMobile: Optional[float] = 0.0
    att: Optional[float] = 0.0
    verizon: Optional[float] = 0.0


class GraphicMultiInterfacePayment(BaseModel):
    name: Optional[str] = None
    paypal: Optional[float] = 0.0
    creditCard: Optional[float] = 0.0
    crypto: Optional[float] = 0.0

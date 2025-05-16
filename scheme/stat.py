from pydantic import BaseModel


class StatInterface(BaseModel):
    total: int
    total_with_active_sub: int
    total_with_discount: int
    total_paid: int

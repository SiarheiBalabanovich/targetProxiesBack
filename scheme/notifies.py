from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from models.notify import TypeNotify


class NotifyScheme(BaseModel):
    id: int
    user_id: int
    is_read: bool
    type: Optional[TypeNotify] = None
    message: str
    date_created: datetime


class NotifyResponse(BaseModel):
    total: int
    notifies: List[NotifyScheme]

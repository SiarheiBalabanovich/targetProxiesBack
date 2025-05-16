from pydantic import BaseModel
from typing import Literal, Optional, List


class Image(BaseModel):
    id: int
    path: str


class PageCreate(BaseModel):
    name: str
    title: str
    content: str
    comments: Optional[str] = None
    visibility: Literal["public", "private"]
    status: Literal["draft", "published"]


class PageUserScheme(BaseModel):
    id: int
    email: str


class PageInterface(PageCreate):
    id: int
    user_created: Optional[PageUserScheme] = None
    user_updated: Optional[PageUserScheme] = None
    date_created: str
    date_updated: Optional[str] = None


class PageInterfaceResponse(BaseModel):
    total: int
    pages: List[PageInterface]

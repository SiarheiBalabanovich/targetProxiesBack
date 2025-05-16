from pydantic import BaseModel
from typing import Optional, Literal, List


class User(BaseModel):
    first_name: str
    last_name: str
    email: str


class UserDetailInfo(BaseModel):
    class Meta:
        from_attributes = True

    survey: Literal[
        "Google", "BlackHatWorld", "Instagram", "Facebook",
        "MP Social", "YouTube", "Email", "Other"
    ]

    survey_detail: Optional[str]
    phone_number: Optional[str]
    city: Optional[str]
    country: Optional[str]


class UserCreate(User):
    password: str


class UserDetailInfoDB(UserDetailInfo):
    user_id: int


class UserAllInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    user_detail: Optional[UserDetailInfo] = None


class UserAllInfoResponse(BaseModel):
    total: int
    users: List[UserAllInfo]

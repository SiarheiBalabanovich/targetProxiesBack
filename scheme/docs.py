from pydantic import BaseModel
from typing import List, Optional


class ParamCreateScheme(BaseModel):
    name: str
    type: str
    description: str


class ParamScheme(ParamCreateScheme):
    id: int


class EndpointSchemeCreate(BaseModel):
    name: str
    api_endpoint: str
    successful_call: dict


class EndpointScheme(EndpointSchemeCreate):
    id: int
    params: Optional[List[ParamScheme]] = None


class EndpointSchemeResponse(BaseModel):
    total: int
    endpoints: List[EndpointScheme]

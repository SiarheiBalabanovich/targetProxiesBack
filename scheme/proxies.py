from pydantic import BaseModel, Field
from typing import Optional, Literal, List


class Modem(BaseModel):
    id: int = Field(..., alias="id")
    name: str = Field(..., alias="name")
    ip: str = Field(..., alias="ip")
    login: Optional[str] = Field(None, alias="login")
    password: Optional[str] = Field(None, alias="password")


class Proxy(BaseModel):
    modem_id: int
    http_ip: str
    http_port: int
    socks5_ip: str
    socks5_port: int
    http_login: Optional[str]
    http_password: Optional[str]
    socks5_login: Optional[str]
    socks5_password: Optional[str]
    location: str


class APILinkInterface(BaseModel):
    rotate: str
    #auto_rotation: str
    proxy_status: str
    change_user: str


class ProxyInterface(Proxy):
    subscription_id: int
    subscription_item_id: int
    proxy_id: int
    discount_code: Optional[str] = None
    discount_amount: Optional[float] = None
    auto_rotation: bool
    modem_name: str
    modem_ip: str
    modem_port: int
    expired: str
    status: bool
    api_links_http: APILinkInterface
    api_links_socks5: APILinkInterface


class ProxyInterfaceResponse(BaseModel):
    total: int
    proxies: List[ProxyInterface]

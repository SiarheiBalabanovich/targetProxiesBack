import datetime

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from logic.authorization.validator import AdminVerifier, TokenVerifier
from logic.proxies.proxy import get_api_links_http, get_api_links_socks5
from crud.proxy import get_user_proxies
from scheme.proxies import ProxyInterface, APILinkInterface, ProxyInterfaceResponse

admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter()


@router.get('/proxies/customer/list')
async def _get_user_proxies(email: str = Depends(verifier),
                            offset: int = 0,
                            limit: int = 10,
                            db: AsyncSession = Depends(get_session)) -> list[Any] | ProxyInterfaceResponse:
    result = []
    data = await get_user_proxies(db, email)

    if not len(data):
        return []

    for (sub_id, sub_item_id, proxy_id, modem_id, carrier,
         carrier_ip, carrier_port, location,
         discount_code, discount_amount, http_log, http_pass, socks5_log, socks5_pass, due_date, is_active,
         http_ip, http_port, http_key, socks5_ip, socks5_port, socks5_key, auto_rotation) in data[offset: limit + offset]:
        api_links_http = APILinkInterface(**get_api_links_http(http_ip, http_port, http_key))
        api_links_socks5 = APILinkInterface(**get_api_links_socks5(http_ip, socks5_port, socks5_key))

        result.append(
            ProxyInterface(
                subscription_id=sub_id,
                subscription_item_id=sub_item_id,
                discount_code=discount_code,
                discount_amount=discount_amount,
                modem_id=modem_id,
                modem_name=carrier,
                modem_ip=carrier_ip,
                modem_port=carrier_port,
                proxy_id=proxy_id,
                http_login=http_log,
                http_password=http_pass,
                socks5_login=socks5_log,
                socks5_password=socks5_pass,
                location=location,
                auto_rotation=auto_rotation,
                http_ip=http_ip,
                http_port=http_port,
                socks5_ip=socks5_ip,
                socks5_port=socks5_port,
                expired=datetime.datetime.strftime(due_date, '%d/%m/%y'),
                status=is_active,
                api_links_http=api_links_http,
                api_links_socks5=api_links_socks5
            )
        )
    return ProxyInterfaceResponse(
        total=len(data),
        proxies=result

    )

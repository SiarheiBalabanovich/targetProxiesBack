import httpx
import aiohttp

import random
from typing import Literal, List
import asyncio

from logic.utils.time import convert_period_to_timestamp
from exceptions.proxy import CreateProxyServiceException, ModemServiceException

rotations = {
    'rotate': '/selling/rotate',
    'proxy_status': '/selling/info',
    'change_user': '/selling/change_user'
}


async def create_proxy(
        proxy_port: int,
        server_port: int,
        email: str,
        period: str = Literal['month', 'week', 'trial']
):
    url = f'https://api.targetedproxies.com:{server_port}/api/admin/gohawks/createProxy/{proxy_port}/{period}/{email}'

    async with aiohttp.ClientSession() as session:
        data = await session.get(
            url=url
        )
        content = await data.json()
        result = {"location": content['location']}
        ip = content['hostIp'].split('http://')[-1].split(':')[0]
        for proxy in content['ports']:
            result.update(
                {
                    f"{proxy['type']}_port": proxy['port'],
                    f"{proxy['type']}_ip": ip,
                    f"{proxy['type']}_key": proxy["api_token"],
                    f"{proxy['type']}_login": proxy['auth'].split(':')[0],
                    f"{proxy['type']}_password": proxy['auth'].split(':')[-1],
                }
            )
    return result


async def delete_proxy(server_port: int, proxy_port: int):
    url = f'http://api.targetedproxies.com:{server_port}/api/admin/gohawks/delete/{proxy_port}'

    async with aiohttp.ClientSession() as session:
        await session.get(
            url=url
        )


async def update_proxy(server_port: int, proxy_port: int, period: str):
    url = f'http://api.targetedproxies.com:{server_port}/api/admin/gohawks/renewSub/{proxy_port}/{period}'
    async with aiohttp.ClientSession() as session:
        await session.get(
            url=url
        )


def rotate(url: str, token: str) -> dict:
    data = {}
    for key, value in rotations.items():
        data[key] = url + value + f'?token={token}'
    return data


def get_api_links_http(http_ip, http_port, token):
    url = f"{http_ip}:{http_port}"
    return rotate(url, token)


def get_api_links_socks5(socks5_ip, socks5_port, token):
    url = f"{socks5_ip}:{socks5_port}"
    return rotate(url, token)

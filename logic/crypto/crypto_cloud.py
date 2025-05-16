import aiohttp

from config.logging_conf import setup_logging
from config.settings import CRYPTO_CLOUD_API_KEY, CRYPTO_CLOUD_SHOP_ID
import logging

logger = logging.getLogger(__name__)
setup_logging(__name__)

async def create_invoice(amount: float, metadata: dict, currency: str = 'USD') -> tuple[str | None, str | None]:
    url = "https://api.cryptocloud.plus/v2/invoice/create"
    headers = {
        "Authorization": f"Token {CRYPTO_CLOUD_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "amount": str(amount),
        "shop_id": CRYPTO_CLOUD_SHOP_ID,
        "currency": currency,
        "add_fields": metadata.copy()
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                link = response_data['result']['link']
                uuid = response_data['result']['uuid']
                return link, uuid
            else:
                response_text = await response.text()
                logger.error(f"SYNC CLOUD ERROR WHILE CREATING CHECKOUT SESSION - {response_text}")
                return None, None


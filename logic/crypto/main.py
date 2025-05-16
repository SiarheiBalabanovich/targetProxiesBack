import aiohttp
from config.settings import CRYPTO_API_KEY, MAIN_HOST

api_key = CRYPTO_API_KEY


async def create_crypto_payment(
        name: str,
        description: str,
        amount: float,
        metadata: dict,
        currency: str = 'USDT'
):
    headers = {
        'Content-Type': 'application/json',
        'X-CC-Api-Key': api_key,
        'X-CC-Version': '2018-03-22',
    }

    json_data = {
        # 'name': name,
        # 'description': description,
        'pricing_type': 'fixed_price',
        'local_price': {
            'amount': amount,
            'currency': currency,
        },
        'metadata': metadata.copy(),
        'cancel_url': f'{MAIN_HOST}/webhook/cancel',
        'success_url': f'{MAIN_HOST}/webhook/success',

    }

    async with aiohttp.ClientSession() as client:
        response = await client.post('https://api.commerce.coinbase.com/charges', headers=headers, json=json_data)

        response.raise_for_status()

        data = await response.json()

        url, payment_id = data['data']['hosted_url'], data['data']['id']
        return url, payment_id

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
import aiohttp

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import async_session
from config.logging_conf import setup_logging
from config.settings import CRYPTO_CLOUD_API_KEY

from models.stripe import Transaction, TransactionStatus

from crud.base import CRUDService

from scripts.stripe_sub_create import create_subscription_stripe_logic

logger = logging.getLogger(__name__)
setup_logging(__name__)


@dataclass
class SyncCryptoCloudService:
    session: AsyncSession = async_session()

    async def get_crypto_orders_not_completed(self) -> list[dict]:
        crud = CRUDService()
        async with self.session as session:
            transactions = await crud.get_by_fields(
                session=session,
                model=Transaction,
                fields={
                    "service": "crypto_cloud",
                    "status": "pending",
                })
            return [
                {
                    "id": transaction.id,
                    "external_id": transaction.created_local_session_id
                }
                for transaction in transactions
            ]

    async def update_status(self, transaction_id: int, status: str):
        crud = CRUDService()
        async with self.session as session:
            await crud.update_fields(
                session=session,
                model=Transaction,
                id=transaction_id,
                **{
                    "status": status
                })

    @staticmethod
    async def get_statuses_crypto_payment() -> dict | None:
        def get_status(status: str) -> bool:
            if status == "paid" or status == "overpaid":
                return True
            else:
                return False

        CRYPTO_CLOUD_URL = f'https://api.cryptocloud.plus/v2/invoice/merchant/list'
        headers = {
            "Authorization": f"Token {CRYPTO_CLOUD_API_KEY}",
            "Content-Type": "application/json",
        }
        time_now = datetime.now()
        start, end = time_now - timedelta(days=1), time_now
        offset = 0
        limit = 100
        params = {
            "start": start.strftime('%d.%m.%Y'),
            "end": end.strftime('%d.%m.%Y'),
            "limit": 100,
            "offset": 0,
        }
        total = float('inf')
        result = {}
        try:
            async with aiohttp.ClientSession() as session:
                while offset <= total:
                    async with session.post(CRYPTO_CLOUD_URL, headers=headers, json=params) as resp:
                        if resp.status == 200:
                            data_json = await resp.json()
                            total = data_json['all_count']

                            for order in data_json['result']:
                                is_expired = (time_now - datetime.strptime(order['created'],'%Y-%m-%d %H:%M:%S.%f')).days >= 1
                                is_charged = get_status(order['status'])
                                result[order['uuid']] = {
                                    "is_expired": is_expired,
                                    "is_charged": is_charged
                                }
                        else:
                            logger.error(
                                f"Ошибка от crypto-cloud при получение информации о платеже: URL: {CRYPTO_CLOUD_URL} \ status_code: {resp.status}"
                            )
                            return None
                    offset = limit
                    limit += offset
                    params['offset'] = offset
                    params['limit'] = limit

        except Exception as e:
            logger.error(f"Ошибка соединения с crypto-cloud - {str(e)}")
            return None
        return result

    async def updater(self):
        transactions = await self.get_crypto_orders_not_completed()
        data_crypto = await self.get_statuses_crypto_payment()

        for transaction in transactions:
            status = None
            try:
                data = data_crypto[transaction['external_id']]
                if isinstance(data, dict):
                    if data['is_charged'] is True:
                        status = TransactionStatus.success
                        subscription = await create_subscription_stripe_logic(
                            transaction_id=transaction['id'],
                            session=self.session
                        )

                    elif data['is_expired'] is True:
                        status = "failed"

                    if status is not None:
                        await self.update_status(
                            transaction_id=transaction['id'],
                            status=status
                        )
                        logger.debug(f"Transaction: {transaction['id']} updated. Status: {status}")

            except Exception as e:
                logger.error(f"Ошибка создание подписки {str(e)}")

    async def executor(self):
        logger.info("Запустил скрипт обновление заказов по крипте (crypto_cloud)")
        while True:
            try:
                await self.updater()
            except Exception as e:
                logger.error(f"Ошибка прогона скрипта на обновление (crypto_cloud). - {getattr(e, 'detail', str(e))}")
            finally:
                await asyncio.sleep(60 * 5)


if __name__ == '__main__':
    service = SyncCryptoCloudService()
    asyncio.run(service.executor())

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
import aiohttp

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import async_session
from config.logging_conf import setup_logging

from models.stripe import Transaction

from crud.base import CRUDService

from scripts.stripe_sub_create import create_subscription_stripe_logic

logger = logging.getLogger(__name__)
setup_logging(__name__)


@dataclass
class SyncCoinbaseService:
    session: AsyncSession = async_session()

    async def get_crypto_orders_not_completed(self) -> list[dict]:
        crud = CRUDService()
        async with self.session as session:
            transactions = await crud.get_by_fields(
                session=session,
                model=Transaction,
                fields={
                    "service": "coinbase",
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
    async def get_status_crypto_payment(coinbase_order_id: str):
        def get_status(timeline: list[dict]):
            return any([i.get('status', "") == "COMPLETED" for i in timeline])

        time_now = datetime.now()
        COINBASE_URL = f'http://api.commerce.coinbase.com/charges/{coinbase_order_id}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(COINBASE_URL) as resp:
                    if resp.status == 200:
                        data_json = await resp.json()
                        is_expired = time_now >= datetime.strptime(data_json['data']['expires_at'],
                                                                   '%Y-%m-%dT%H:%M:%SZ')
                        is_charged = get_status(data_json['data']['timeline'])

                        return {
                            "is_expired": is_expired,
                            "is_charged": is_charged
                        }
                    else:
                        logger.error(
                            f"Ошибка от coinbase при получение информации о платеже: URL: {COINBASE_URL} \ status_code: {resp.status}")
        except Exception as e:
            logger.error(f"Ошибка соединения с coinbase - {str(e)}")

    async def updater(self):
        transactions = await self.get_crypto_orders_not_completed()

        for transaction in transactions:
            status = None
            data = await self.get_status_crypto_payment(transaction['external_id'])
            try:
                if isinstance(data, dict):
                    if data['is_charged'] is True:
                        status = "success"
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
        logger.info("Запустил скрипт обновление заказов по крипте (coinbase)")
        while True:
            try:
                await self.updater()
            except Exception as e:
                logger.error(f"Ошибка прогона скрипта на обновление (coinbase). - {str(e)}")
            finally:
                await asyncio.sleep(60 * 5)


if __name__ == '__main__':
    service = SyncCoinbaseService()
    asyncio.run(service.executor())

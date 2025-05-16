from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.stripe import TransactionOrder, Transaction, StripeAccount


async def get_transaction_order(
        transaction_id: int,
        session: AsyncSession
):

    query = select(
        TransactionOrder
    ).join(
        TransactionOrder.modem
    ).join(
        TransactionOrder.transaction
    ).join(
        Transaction.user_stripe
    ).where(
        TransactionOrder.transaction_id == transaction_id
    ).options(
        selectinload(
            TransactionOrder.modem
        ),
        selectinload(TransactionOrder.transaction),
        selectinload(TransactionOrder.transaction).selectinload(Transaction.user_stripe)
    )

    result = await session.execute(query)

    if transaction_order := result.scalar_one():
        return {
            "id": transaction_order.id,
            "quantity": transaction_order.quantity,
            "price": transaction_order.transaction.amount,
            "customer_id": transaction_order.transaction.user_stripe.stripe,
            "duration": transaction_order.period_str.split()[1].strip(),
            "duration_count": int(transaction_order.period_str.split()[0].strip()),
            "modem_name": transaction_order.modem.name,
            "modem_id": transaction_order.modem.id,
            "discount_id": transaction_order.discount_id,
            "period_str": transaction_order.period_str,
            "user_id": transaction_order.transaction.user_stripe.user_id,
            "stripe_account_id": transaction_order.transaction.user_stripe.id,
        }
    return None
from sqlalchemy.ext.asyncio import AsyncSession

from crud.stripe import create_subscription_stripe
from logic.stripe.stripe_script import create_subscription_stripe_script_logic
from crud.transaction import get_transaction_order


async def create_subscription_stripe_logic(transaction_id: int, session: AsyncSession):
    async with session as _session:
        sub_data = await get_transaction_order(transaction_id=transaction_id, session=_session)

        subscription = await create_subscription_stripe_script_logic(
            **sub_data,
            cancel_at_period_end=True
        )
        await create_subscription_stripe(
            stripe_subscription=subscription,
            stripe_account_id=sub_data['stripe_account_id'],
            extend=False,
            discount_id=sub_data['discount_id'],
            carrier_id=sub_data['modem_id'],
            user_id=sub_data['user_id'],
            location="Any location",
            period_str=sub_data['period_str'],
            payment_per_period=sub_data['price'],
            db=_session
        )

    return subscription

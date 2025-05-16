import uuid
from typing import Tuple

from fastapi.exceptions import HTTPException

from crud.base import CRUDService
from crud.notify import create_notify
from crud.proxy import get_subscription_proxies
from crud.stripe import create_subscription_stripe
from logic.discount.update import update_discount
from logic.proxies.proxy import update_proxy

from logic.stripe.customer import create_params
from logic.stripe.main import client
from logic.stripe.payment import get_payment_by_invoice
from logic.utils.time import convert_from_timestamp
from models.discounts import Discount
from models.stripe import Transaction, Subscription, SubscriptionPaymentData, SubscriptionItem, TransactionOrder
from models.user import User
from models.stripe import StripeAccount

import ast

from sqlalchemy.ext.asyncio import AsyncSession
from stripe._subscription import Subscription as StripeSubscription
from stripe._event import Event


async def actions_update_subscription(event: Event,
                                      subscription_stripe: StripeSubscription,
                                      subscription_db: Subscription,
                                      user: User,
                                      customer: StripeAccount,
                                      plan: dict,
                                      db: AsyncSession) -> Tuple[int, int]:
    crud = CRUDService()

    uid = str(uuid.uuid4())

    transaction_id = await crud.create(db, Transaction, **{
        'uid': uid,
        'user_stripe_id': customer.id,
        'invoice_stripe_id': event.data.object.id,
        'created_local_session_id': None,
        'amount': event.data.object.total / 100,
        'status': 'success'
    })
    await crud.update_fields(db, Subscription, subscription_db.id, **{
        'date_end': convert_from_timestamp(subscription_stripe.ended_at),
        'period_start': convert_from_timestamp(subscription_stripe.current_period_start),
        'period_end': convert_from_timestamp(subscription_stripe.current_period_end)
    })

    await create_notify(customer.user_id, f"Successfully renewed subscription. Check your orders", type="proxy_prolong")

    subscription_id = getattr(subscription_db, 'id', subscription_db)
    period_normal = plan['interval'].lower()
    if period_normal == 'day':
        period_normal = 'trial'

    proxies = await get_subscription_proxies(db, subscription_id)
    for proxy in proxies:
        await update_proxy(
            proxy_port=proxy.get('proxy_port'),
            server_port=proxy.get('port'),
            period=period_normal,
        )

    await crud.update_fields(db, Subscription, subscription_id,
                             **{
                                 'payment_per_period': event.data.object.total / 100,
                                 'period_str': f"{plan['interval_count']} {plan['interval'].lower()}"
                             })
    return transaction_id, subscription_id


async def actions_create_subscription(event: Event,
                                      subscription_stripe: StripeSubscription,
                                      customer: StripeAccount,
                                      plan: dict,
                                      db: AsyncSession) -> Tuple[int, int]:
    crud = CRUDService()

    created_local_session_id = subscription_stripe.metadata.get('local_uid')
    transaction = await crud.get_by_field(db, Transaction, 'uid', created_local_session_id,
                                          single=True)
    if transaction is None:
        raise HTTPException(status_code=404, detail=f"Subscription from other service")
    transaction_id = transaction.id

    await crud.update_fields(db, Transaction, transaction_id, **{
        'invoice_stripe_id': event.data.object.id,
        'status': "success"
    })
    discount_id = subscription_stripe.metadata.get('local_discount_id')
    carrier_id = subscription_stripe.metadata.get('carrier_id', 1)
    user_id = subscription_stripe.metadata.get('user_id')
    location = subscription_stripe.metadata.get('location', 'Unknown')
    extend = ast.literal_eval(subscription_stripe.metadata.get('auto_extended', "True"))

    if isinstance(discount_id, str):
        discount_id = int(discount_id)
    if isinstance(user_id, str):
        user_id = int(user_id)

    try:
        subscription_id = await create_subscription_stripe(subscription_stripe,
                                                           customer.id,
                                                           extend,
                                                           discount_id,
                                                           carrier_id,
                                                           user_id,
                                                           location,
                                                           f"{plan['interval_count']} {plan['interval']}",
                                                           transaction.amount,
                                                           db)
    except Exception as e:
        raise e
    payment_data = await get_payment_by_invoice(event.data.object.id)
    payment_data['subscription_id'] = subscription_id

    await crud.create(db, SubscriptionPaymentData, **payment_data)

    if discount_id:
        await update_discount(discount_id, db)

    transaction_order = await crud.get_by_field(db, TransactionOrder, 'transaction_id', transaction_id, single=True)
    if transaction_order:
        payment = payment_data.get('method') if payment_data.get('method').lower() != 'card' else payment_data.get(
            'payment_data', {}).get('brand')

        await crud.update_fields(db, TransactionOrder, transaction_order.id, **{'payment_method': payment.lower()})

    await client.subscriptions.update_async(subscription_stripe.id, create_params(**{
        'cancel_at_period_end': not extend
    }))

    return transaction_id, subscription_id


async def actions_delete_subscription(subscription_db: Subscription,
                                      user: User,
                                      db: AsyncSession):
    crud = CRUDService()

    if subscription_db is not None:
        await crud.update_fields(db, Subscription, subscription_db.id, **{
            'is_active': False
        })
        await create_notify(user.id, f"Subscription deleted", type="proxy_deleted")
        items = await crud.get_by_field(db, SubscriptionItem, 'subscription_id', subscription_db.id)

        for item in items:
            await crud.update_fields(db, SubscriptionItem, item.id, **{'is_active': False})
    else:
        raise HTTPException(status_code=404, detail="Subscription from another service")

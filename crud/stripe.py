from sqlalchemy.orm import join

from crud.base import CRUDService
from crud.notify import create_notify
from models.discounts import Discount
from models.stripe import Subscription, SubscriptionItem, StripeAccount, SubscriptionPaymentData, SubscriptionCharge, \
    Transaction, TransactionOrder
from models.proxies import Modem, Proxy
from sqlalchemy.ext.asyncio import AsyncSession
from logic.utils.time import convert_from_timestamp
from sqlalchemy import select, extract, cast, func, Interval, distinct
from logic.proxies.proxy import create_proxy
from models.user import User


async def create_subscription_stripe(
        stripe_subscription,
        stripe_account_id,
        extend,
        discount_id,
        carrier_id,
        user_id,
        location,
        period_str,
        payment_per_period,
        db: AsyncSession
):
    crud = CRUDService()

    user = await crud.get_by_field(db, User, 'id', int(user_id), single=True)
    carrier = await crud.get_by_field(db, Modem, 'id', int(carrier_id), single=True)

    sub_items = stripe_subscription['items']['data']

    subscription_id = await crud.create(db, Subscription, **{
        'stripe_subscription_id': stripe_subscription.id,
        'stripe_account_id': stripe_account_id,
        'is_active': True,
        'auto_extend': extend,
        'date_start': convert_from_timestamp(stripe_subscription.start_date),
        'date_end': convert_from_timestamp(stripe_subscription.ended_at),
        'period_start': convert_from_timestamp(stripe_subscription.current_period_start),
        'period_end': convert_from_timestamp(stripe_subscription.current_period_end),
        'discount_id': discount_id,
        'period_str': period_str,
        'payment_per_period': payment_per_period,
    })

    period_normal = period_str.split()[-1].lower()
    if period_normal == 'day':
        period_normal = 'trial'

    for item in sub_items:
        proxy = await create_proxy(
            proxy_port=carrier.proxy_port,
            server_port=carrier.port,
            email=user.email,
            period=period_normal,
        )

        proxy['modem_id'] = carrier.id

        proxy_id = await crud.create(db, Proxy, **proxy)

        item_id = await crud.create(db, SubscriptionItem, **{
            'stripe_item_id': item.id,
            'subscription_id': subscription_id,
            'proxy_id': proxy_id
        })
        await create_notify(int(user_id), f"New proxy gained. Check your purchases", type="proxy_buy")

    return subscription_id


async def get_subscription_items(db: AsyncSession, subscription_id: int):
    query = (select(
        SubscriptionItem,
        Proxy,
        Modem
    ).join(
        SubscriptionItem.proxy
    ).join(
        Proxy.modem
    ).where(
        SubscriptionItem.subscription_id == subscription_id,
        SubscriptionItem.is_active == True
    ))

    result = await db.execute(query)

    return result.all()


async def get_user_subscriptions(db: AsyncSession, email: str):
    subquery = (
        select(
            TransactionOrder.id.label('order_id'),
            Subscription.id.label('subscription_id'),
            Subscription.payment_per_period.label('payment_per_period'),
            Subscription.period_str.label('period_str'),
            Subscription.period_end.label('period_end'),
            extract('day', cast((Subscription.period_end - func.now()), Interval)).label('next_payment'),
            Subscription.auto_extend.label('auto_extend'),
        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .outerjoin(Subscription.payment)
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .join(Transaction.transaction_order)
        .where(
            User.email == email,
            Subscription.is_active == True,
            Transaction.status == 'success'
        )
        .group_by(
            TransactionOrder.id,
            Subscription.id,
            )
        .subquery()
    )

    query = (select(
        subquery.c.order_id,
        subquery.c.subscription_id,
        subquery.c.payment_per_period,
        SubscriptionPaymentData.payment_data,
        subquery.c.period_str,
        subquery.c.period_end,
        subquery.c.next_payment,
        subquery.c.auto_extend

    ).outerjoin(
        SubscriptionPaymentData,
        SubscriptionPaymentData.subscription_id == subquery.c.subscription_id
        )
    ).order_by(subquery.c.order_id.desc())

    result = await db.execute(query)

    return result.fetchall()


async def get_subscription_price_bought(db, subscription_id: int):
    query_transaction = (
        select(
            Subscription,
            Transaction.amount
        )
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .where(
            Subscription.id == subscription_id,
            Transaction.status == 'success',

        ).order_by(Transaction.id).limit(1)
    )

    query_items = (
        select(
            func.count(Subscription.items)
        )
        .select_from(Subscription)
        .join(Subscription.items)
        .where(
            Subscription.id == subscription_id,
        ).group_by(Subscription.id)
    )
    result_items = await db.execute(query_items)
    count_items = result_items.fetchone().count

    result_transaction = await db.execute(query_transaction)
    _, amount = result_transaction.fetchone()

    return amount / count_items


async def get_user_orders(db: AsyncSession, email: str, active=None):
    if active is not None:
        active_clause = (
            Subscription.is_active == active,
            SubscriptionItem.is_active == active
        )
    else:
        active_clause = (
            Subscription.is_active != None,
            SubscriptionItem.is_active != None
        )

    query = (
        select(
            Subscription.id.label('subscription_id'),
            SubscriptionItem.id.label('subscription_item_id'),
            Modem.name,
            Subscription.period_str,
            Subscription.period_end,
            Subscription.date_start,
            Discount.discount_amount,
            Discount.code,
            SubscriptionItem.is_active,
            SubscriptionPaymentData.payment_data
        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .outerjoin(Subscription.payment)
        .outerjoin(Subscription.discount)
        .where(
            User.email == email,
            *active_clause
        )
        .order_by(SubscriptionItem.id)
    )

    result = await db.execute(query)

    return result.fetchall()


async def get_subscription_charges(db: AsyncSession, email: str):
    query = (
        select(
            Transaction.date_created,
            Subscription.id,
            SubscriptionItem.id,
            TransactionOrder.id,
            Modem.name,
            Proxy.id,
            Proxy.location,
            SubscriptionCharge.interval,
            SubscriptionCharge.interval_count,
            Discount.discount_amount,
            Transaction.amount

        ).select_from(
            User
        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .join(Transaction.transaction_order)
        .outerjoin(Subscription.discount)
        .where(
            User.email == email,
            Transaction.status == 'success'
        ).order_by(Transaction.date_created.desc())
    )

    result = await db.execute(query)

    return result.all()


async def get_last_user_subscription(db: AsyncSession, email: str):
    query = (
        select(
            func.json_build_object(
                "order_id", TransactionOrder.id,
                "subscription_id", Subscription.id,
                "subscription_item_id", SubscriptionItem.id,
                "auto_extend", Subscription.auto_extend,
                "payment_date", Subscription.period_start,
                "date_end", Subscription.period_end,
                "next_payment", extract('day', cast((Subscription.period_end - func.now()), Interval)),
                "payment_per_period", Subscription.payment_per_period,
                "payment_method", TransactionOrder.payment_method,

                "modem_name", Modem.name,
                "proxy_id", Proxy.id,
                "proxy_location", Proxy.location,
                "login", Proxy.login,
                "password", Proxy.password,
                "interval", SubscriptionCharge.interval,
                "interval_count", SubscriptionCharge.interval_count,
                "amount", Transaction.amount
            )
        ).select_from(
            User
        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .join(Subscription.charges)
        .join(Subscription.payment)
        .join(SubscriptionCharge.transaction)
        .join(Transaction.transaction_order)
        .outerjoin(Subscription.discount)
        .where(
            User.email == email,
            Transaction.status == 'success',
            Subscription.is_active == True
        ).order_by(Subscription.id.desc(), Transaction.id.desc())
    )

    result = await db.execute(query)

    return result.fetchall()


async def get_users_subscriptions_active(db: AsyncSession):
    query = (
        select(
            func.count(distinct(User.id)).label("total_users_with_active_subscriptions"),
        )
        .select_from(
            join(User, StripeAccount, User.user_stripe)
        )
        .join(Subscription, StripeAccount.subscription)
        .where(
            Subscription.is_active == True,
            User.is_active == True
        )
    )

    result = await db.execute(query)
    return result.scalar_one()


async def get_length_users_with_discount(db: AsyncSession):
    query = (
        select(
            func.count(distinct(User.id))
        )

        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .where(
            Subscription.discount_id != None,
            User.is_active == True
        )
    )
    result = await db.execute(query)
    return result.scalar_one()


async def get_total_users_with_sub(db: AsyncSession):
    query = (
        select(
            func.count(distinct(User.id))
        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .where(User.is_active == True)
    )
    result = await db.execute(query)
    return result.scalar_one()


async def get_all_orders(db: AsyncSession,
                         email=None,
                         status=None,
                         query_search=None,
                         carrier=None,
                         payment_method=None,
                         order_date_start=None,
                         order_date_end=None):

    clause = []

    if status is not None:
        clause.append(
            Transaction.status == status,
        )
    if email is not None:
        clause.append(
            User.email == email
        )
    if query_search is not None:
        clause.append(
            User.first_name.ilike(f"%{query_search}%") |
            User.last_name.ilike(f"%{query_search}%") |
            User.email.ilike(f"%{query_search}%") |
            Discount.code.ilike(f"%{query_search}%") |
            Modem.name.ilike(f"%{query_search}%") |
            TransactionOrder.payment_method.ilike(f"%{query_search}%")
        )
    if carrier is not None:
        clause.append(
            Modem.name == carrier
        )
    if payment_method is not None:
        clause.append(
            TransactionOrder.payment_method == payment_method
        )
    if order_date_start is not None:
        clause.append(
            Transaction.date_created >= order_date_start
        )
    if order_date_end is not None:
        clause.append(
            Transaction.date_created <= order_date_end
        )

    query = (
        select(
            TransactionOrder.id,
            TransactionOrder.payment_link,
            Transaction.service,

            User.first_name,
            User.last_name,
            User.email,

            Transaction.date_created,
            Modem.name,
            TransactionOrder.period_str,
            Transaction.amount,
            Discount.code,
            Discount.discount_amount,
            TransactionOrder.payment_method,
            Transaction.status
        )
        .select_from(
            TransactionOrder
        )
        .join(TransactionOrder.transaction)
        .join(TransactionOrder.modem)
        .outerjoin(TransactionOrder.discount)
        .join(Transaction.user_stripe)
        .join(StripeAccount.user)
        .where(
            *clause
        )
        .order_by(TransactionOrder.id.desc())
    )

    result = await db.execute(query)

    return result.fetchall()

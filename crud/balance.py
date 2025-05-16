from models.stripe import Subscription, SubscriptionItem, StripeAccount, SubscriptionCharge, Transaction, \
    TransactionOrder
from models.user import User, UserCryptoBalance, UserDetailInfo
from models.proxies import Proxy, Modem

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, aliased, joinedload, selectinload
from sqlalchemy import select, or_, func, join, cast, extract, DateTime, Integer, distinct
from sqlalchemy.sql.functions import concat
from sqlalchemy import Interval

from logic.utils.time import last_day_of_month


async def get_purchases_balance(db: AsyncSession, email: str):
    user_alias = aliased(User)
    user_crypto_alias = aliased(UserCryptoBalance)
    stripe_account_alias = aliased(StripeAccount)
    subscription_alias = aliased(Subscription)

    last_day = last_day_of_month()

    payment_in_period = cast(
        last_day.day // cast(func.date_part('day', subscription_alias.period_end - subscription_alias.period_start),
                             Integer), Integer)

    query = select(
        func.sum(payment_in_period * subscription_alias.payment_per_period).label("payment_per_month"),
        func.sum(user_crypto_alias.amount).label("total_crypto_balance"),
    ).select_from(
        join(
            user_alias,
            stripe_account_alias,
            user_alias.id == stripe_account_alias.user_id
        )
        .outerjoin(
            subscription_alias,
            stripe_account_alias.id == subscription_alias.stripe_account_id
        )
        .outerjoin(
            user_crypto_alias,
            user_alias.id == user_crypto_alias.user_id
        )
    ).where(
        user_alias.email == email,
        subscription_alias.auto_extend == True,
        subscription_alias.is_active == True,
        subscription_alias.period_end <= last_day,
        or_(subscription_alias.trial_end == None, subscription_alias.trial_end <= last_day)
    ).group_by(
        user_alias.id
    )

    results = await db.execute(query)
    return results.all()


async def get_count_purchases(db: AsyncSession, email: str):
    query = (
        select(
            func.count(distinct(TransactionOrder.id))
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
            User.email == email,
            Transaction.status == 'success',
        )
    )
    results = await db.execute(query)
    return results.scalar_one_or_none()


async def get_closest_payments(db: AsyncSession, email: str):
    query = (
        select(
            Subscription.id,
            extract('day', cast((Subscription.period_end - func.now()), Interval)),
            SubscriptionItem.id,
            Modem.name,
            Proxy.location
        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .where(
            User.email == email,
            Subscription.is_active == True,
            Subscription.auto_extend == True
        )
        .order_by(Subscription.period_end)
    )

    result = await db.execute(query)

    return result.fetchall()


async def get_last_payments(db: AsyncSession, email: str):
    query = (
        select(
            TransactionOrder.id,
            Subscription.id,
            Subscription.is_active,
            SubscriptionItem.id,
            Transaction.amount,
            Transaction.date_created,
            Modem.name,
            Proxy.location,
            Proxy.http_ip,
            Proxy.http_port,
            Proxy.socks5_ip,
            Proxy.socks5_port

        )
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .join(Transaction.transaction_order)
        .where(
            User.email == email,
        )
        .order_by(TransactionOrder.id.desc())
    )

    result = await db.execute(query)

    return result.fetchone()


async def get_all_payment_graphics(db: AsyncSession):
    query = (
        select(User)
        .outerjoin(User.user_detail)
        .outerjoin(User.user_stripe)
        .outerjoin(StripeAccount.subscription)
        .outerjoin(Subscription.items)
        .outerjoin(Subscription.charges)
        .outerjoin(SubscriptionCharge.transaction)
        .outerjoin(SubscriptionItem.proxy)
        .outerjoin(Proxy.modem)
        .outerjoin(Subscription.payment)
        .options(
            joinedload(User.user_detail),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription).joinedload(Subscription.items),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription).joinedload(Subscription.charges),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription).joinedload(
                Subscription.charges).joinedload(SubscriptionCharge.transaction),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription).joinedload(
                Subscription.items).joinedload(SubscriptionItem.proxy),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription).joinedload(
                Subscription.items).joinedload(SubscriptionItem.proxy).joinedload(Proxy.modem),
            joinedload(User.user_stripe).joinedload(StripeAccount.subscription).joinedload(Subscription.payment),
        )
    )
    result = await db.execute(query)

    return result.unique().scalars().all()

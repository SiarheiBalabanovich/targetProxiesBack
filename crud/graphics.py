from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from models.user import User, UserDetailInfo
from models.discounts import Discount
from models.stripe import Subscription, SubscriptionItem, StripeAccount, SubscriptionPaymentData, SubscriptionCharge, \
    Transaction
from models.proxies import Modem, Proxy
from sqlalchemy import select, or_, func, cast, JSON, extract, Integer, Float
from datetime import datetime


async def get_revenue(db: AsyncSession, period):
    trans_query = Transaction.status == 'success'
    date_now = datetime.utcnow().date()

    if period == 'month' or period == 'year':
        period = 'month'

        where_query = (
            trans_query,
            cast(extract('year', Transaction.date_created), Integer) == date_now.year
        )
    elif period == 'week':
        period = 'day'

        where_query = (
            trans_query,
            cast(extract('year', Transaction.date_created), Integer) == date_now.year,
            cast(extract('week', Transaction.date_created), Integer) == date_now.isocalendar().week
        )
    else:
        where_query = (trans_query,)

    query = (
        select(
            cast(func.sum(Transaction.amount), Float),
            cast(extract(period, Transaction.date_created), Integer)
        ).where(
            *where_query
        )
        .group_by(extract(period, Transaction.date_created))
    )

    result = await db.execute(query)

    return result.all()


async def get_survey(db: AsyncSession, period: str):
    date_now = datetime.utcnow().date()

    if period == 'month' or period == 'year':

        where_query = (
            cast(extract('year', User.date_created), Integer) == date_now.year,
        )
    elif period == 'week':

        where_query = (
            cast(extract('year', User.date_created), Integer) == date_now.year,
            cast(extract('week', User.date_created), Integer) == date_now.isocalendar().week
        )
    else:
        where_query = ()

    query_count = (
        select(
            func.count(
                func.distinct(
                    User.id
                )
            )
        )
        .join(User.user_detail)
        .where(*where_query)
    )

    result_count = await db.execute(query_count)
    total_count = result_count.scalar_one()

    query = (
        select(
            UserDetailInfo.survey,
            cast(func.count(UserDetailInfo.survey) / total_count, Float) * 100,
        )
        .select_from(User)
        .join(User.user_detail)
        .where(*where_query)
        .group_by(UserDetailInfo.survey)

    )

    result = await db.execute(query)

    return result.all()


async def get_sales_location(db: AsyncSession, period: str):
    date_now = datetime.utcnow().date()

    if period == 'month' or period == 'year':

        where_query = (
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
        )
    elif period == 'week':

        where_query = (
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
            cast(extract('week', Subscription.date_start), Integer) == date_now.isocalendar().week
        )
    else:
        where_query = ()

    sub_query = (
        select(
            func.count(
                func.distinct(
                    SubscriptionItem.id
                )
            )
        ).select_from(
            Subscription
        )
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .where(*where_query)
    )

    result_count = await db.execute(sub_query)
    total_count = result_count.scalar_one()

    query = (
        select(
            Proxy.location,
            cast(func.count(Proxy.location) / total_count, Float) * 100,
        )
        .select_from(Subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .where(*where_query)
        .group_by(Proxy.location)
    )

    result = await db.execute(query)

    return result.all()


async def get_sales_carrier(db: AsyncSession, period: str):
    date_now = datetime.utcnow().date()

    trans_query = Transaction.status == 'success'

    if period == 'month' or period == 'year':
        period = 'month'
        where_query = (
            trans_query,
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
        )
    elif period == 'week':
        period = 'day'

        where_query = (
            trans_query,
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
            cast(extract('week', Subscription.date_start), Integer) == date_now.isocalendar().week
        )
    else:
        where_query = (trans_query,)

    sub_query = (

        select(
            Modem.name.label('modem'),
            Transaction.id,
            Transaction.amount.label('amount'),
            cast(extract(period, Subscription.date_start), Integer).label('period'),
        )
        .select_from(Subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .join(Proxy.modem)
        .where(*where_query)
        .distinct(Transaction.id)
    ).subquery()

    query = (
        select(
            sub_query.c.modem,
            func.sum(sub_query.c.amount),
            sub_query.c.period
        )
        .group_by(sub_query.c.period, sub_query.c.modem)
    )

    result = await db.execute(query)

    return result.all()


async def get_revenue_source(db: AsyncSession, period: str):
    date_now = datetime.utcnow().date()

    trans_query = Transaction.status == 'success'

    if period == 'month' or period == 'year':
        period = 'month'
        where_query = (
            trans_query,
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
        )
    elif period == 'week':
        period = 'day'

        where_query = (
            trans_query,
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
            cast(extract('week', Subscription.date_start), Integer) == date_now.isocalendar().week
        )
    else:
        where_query = (trans_query,)

    sub_query = (

        select(
            SubscriptionPaymentData.method.label('method'),
            Transaction.id,
            Transaction.amount.label('amount'),
            cast(extract(period, Subscription.date_start), Integer).label('period'),
        )
        .select_from(Subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .join(Subscription.payment)
        .join(Proxy.modem)
        .where(*where_query)
        .distinct(Transaction.id)
    ).subquery()

    query = (
        select(
            sub_query.c.method,
            func.sum(sub_query.c.amount),
            sub_query.c.period
        )
        .group_by(sub_query.c.period, sub_query.c.method)
    )

    result = await db.execute(query)

    return result.all()


async def get_sales_customer(db: AsyncSession, period: str):
    date_now = datetime.utcnow().date()

    trans_query = Transaction.status == 'success'

    if period == 'month' or period == 'year':
        period = 'month'
        where_query = (
            trans_query,
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
        )
    elif period == 'week':
        period = 'day'

        where_query = (
            trans_query,
            cast(extract('year', Subscription.date_start), Integer) == date_now.year,
            cast(extract('week', Subscription.date_start), Integer) == date_now.isocalendar().week
        )
    else:
        where_query = (trans_query,)

    sub_query = (

        select(
            User.id.label('user_id'),
            func.concat(
                func.substring(User.first_name, 1, 1),
                func.substring(User.last_name, 1, 1)
            ).label('name'),
            Transaction.id,
            Transaction.amount.label('amount'),
        )
        .select_from(User)
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Subscription.charges)
        .join(SubscriptionCharge.transaction)
        .join(Proxy.modem)
        .where(*where_query)
        .distinct(Transaction.id)
    ).subquery()

    query = (
        select(
            sub_query.c.name,
            func.sum(sub_query.c.amount),
        )
        .group_by(sub_query.c.user_id, sub_query.c.name)
    )

    result = await db.execute(query)

    return result.all()

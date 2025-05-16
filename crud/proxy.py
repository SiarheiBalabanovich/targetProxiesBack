from models.discounts import Discount
from models.stripe import Subscription, SubscriptionItem, StripeAccount
from models.proxies import Modem, Proxy
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, func

from models.user import User


async def get_user_proxies(db: AsyncSession, email: str):
    query = (
        select(
            Subscription.id,
            SubscriptionItem.id,
            Proxy.id,
            Modem.id,
            Modem.name,
            Modem.ip,
            Modem.port,
            Proxy.location,
            Discount.code,
            Discount.discount_amount,
            Proxy.http_login,
            Proxy.http_password,
            Proxy.socks5_login,
            Proxy.socks5_password,
            Subscription.period_end,
            Subscription.is_active,
            Proxy.http_ip,
            Proxy.http_port,
            Proxy.http_key,
            Proxy.socks5_ip,
            Proxy.socks5_port,
            Proxy.socks5_key,
            Proxy.auto_rotation

        ).select_from(User)
        .join(User.user_stripe)
        .join(StripeAccount.subscription)
        .join(Subscription.items)
        .outerjoin(Subscription.discount)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .where(
            User.email == email,
            SubscriptionItem.is_active == True
        )
        .order_by(Subscription.id.desc())
    )

    result = await db.execute(query)

    return result.fetchall()


async def get_subscription_proxies(db: AsyncSession, subscription_id: int):

    query = (
        select(
            func.concat(Modem.ip, ':', Modem.port).label('carrier_ip'),
            Modem.login.label('carrier_username'),
            Modem.password.label('carrier_password'),
            Modem.proxy_port.label('proxy_port'),
            Modem.port.label('modem_port'),
            Proxy.position.label('position'),
            func.concat(Proxy.login, ':', Proxy.password).label('auth_entry'),
            func.json_build_object(
                "type", "http",
                'id', Proxy.http_id
            ).label('http_proxy'),
            func.json_build_object(
                "type", "socks5",
                "id", Proxy.socks5_id
            ).label('socks5_proxy')



        ).select_from(Subscription)
        .join(Subscription.items)
        .join(SubscriptionItem.proxy)
        .join(Proxy.modem)
        .where(
            Subscription.id == subscription_id,
            SubscriptionItem.is_active == True
        )
    )

    result = await db.execute(query)

    column_names = [column for column in result.keys()]

    rows = [dict(zip(column_names, row)) for row in result.fetchall()]

    return rows
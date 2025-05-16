import datetime
from typing import Literal, Optional, List

from fastapi import Depends, APIRouter
from fastapi.exceptions import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session

from crud.base import CRUDService
from crud.stripe import (
    get_subscription_items,
    get_user_subscriptions,
    get_subscription_charges,
    get_last_user_subscription, get_all_orders
)
from crud.user import get_user_by_id

from scheme.subscription import (
    SubscriptionInterface,
    OrderInterface,
    SubscriptionPayment,
    SubscriptionLast,
    OrderInterfaceResponse,
    SubscriptionInterfaceResponse,
    SubscriptionPaymentResponse
)

from logic.authorization.validator import TokenVerifier, AdminVerifier
from logic.utils.time import convert_from_timestamp
from logic.stripe.subscription import update_subscription_plan, stripe_delete_item, stripe_delete_subscription

from models.stripe import Subscription, SubscriptionItem

router = APIRouter()

verifier = TokenVerifier()
admin_verifier = AdminVerifier()


@router.get('/subscription/customer/list')
async def _get_user_subscriptions(
        email: str = Depends(verifier),
        user_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 10,
        db: AsyncSession = Depends(get_session)) -> SubscriptionInterfaceResponse:
    result = []
    if user_id is not None:
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        email = user.email

    subscriptions = await get_user_subscriptions(db, email)
    for order_id, sub_id, payment, payment_data, period_str, period_end, expires, auto_extend, in subscriptions[
                                                                                    offset: offset + limit]:
        result.append(
            SubscriptionInterface(
                auto_extend=auto_extend,
                order_id=order_id,
                subscription_id=sub_id,
                payment_per_period=payment,
                payment_data=payment_data,
                period_str=period_str,
                due_date=datetime.datetime.strftime(period_end, '%d/%m/%y'),
                expires=expires
            )
        )
    return SubscriptionInterfaceResponse(
        total=len(subscriptions),
        subscriptions=result
    )


@router.get('/subscription/customer/order/list')
async def _get_user_orders(email: str = Depends(verifier),
                           user_id: Optional[int] = None,
                           offset: int = 0,
                           limit: int = 10,
                           status: Literal['pending', 'success', 'failed'] = None,
                           db: AsyncSession = Depends(get_session)) -> OrderInterfaceResponse:
    if user_id is not None:
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        email = user.email

    orders = await get_all_orders(db, email=email, status=status)
    result = []

    for id_, payment_link, payment_service, first_name, last_name, email, \
            created, carrier, period_str, \
            amount, discount_code, discount_amount, \
            payment_method, status in orders[offset: offset + limit]:
        result.append(
            OrderInterface(
                order_id=id_,
                payment_link=payment_link,
                first_name=first_name,
                last_name=last_name,
                email=email,
                date_created=datetime.datetime.strftime(created, "%d/%m/%y"),
                carrier=carrier,
                amount=amount,
                period_str=period_str,
                discount_amount=discount_amount,
                discount_code=discount_code,
                payment_method=payment_method,
                status=status.value
            )
        )
    return OrderInterfaceResponse(
        total=len(orders),
        orders=result
    )


@router.get('/subscription/customer/charges/list')
async def _get_customer_charges_list(email: str = Depends(verifier),
                                     user_id: Optional[int] = None,
                                     offset: int = 0,
                                     limit: int = 10,
                                     db: AsyncSession = Depends(get_session)) -> SubscriptionPaymentResponse:
    result = []
    if user_id is not None:
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        email = user.email

    data = await get_subscription_charges(db, email)

    if not len(data):
        raise HTTPException(status_code=404, detail="Payments not found")

    for (payment_date, sub_id, sub_item_id, order_id, modem_name, proxy_id, proxy_location,
         interval, interval_count, discount, amount) in data[offset: offset + limit]:
        result.append(
            SubscriptionPayment(
                payment_date=datetime.datetime.strftime(payment_date, "%d/%m/%y"),
                subscription_id=sub_id,
                subscription_item_id=sub_item_id,
                order_id=order_id,
                modem_name=modem_name,
                proxy_location=proxy_location,
                proxy_id=proxy_id,
                period_str=f"{interval_count} {interval}",
                discount=discount,
                amount=amount
            )
        )
    return SubscriptionPaymentResponse(
        total=len(data),
        payments=result
    )


@router.get('/subscription/customer/last')
async def _get_customer_last_sub(
        email: str = Depends(verifier),
        user_id: Optional[int] = None,
        db: AsyncSession = Depends(get_session)) -> List[SubscriptionLast]:
    crud = CRUDService()

    if user_id is not None:
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        email = user.email

    subscriptions = await get_last_user_subscription(db, email)

    cache_length = {}
    items_cache = set()
    result = []

    for data in subscriptions:

        data = data[0]

        if not (data['subscription_id'] in data):
            items_cache.add(data['subscription_id'])
        else:
            continue

        if (length := cache_length.get(data['subscription_id'])) is None:
            items = await crud.get_by_fields(db, SubscriptionItem, {
                'subscription_id': data['subscription_id'],
                'is_active': True
            })
            length = len(items)
            cache_length[data['subscription_id']] = length

        data['date_end'] = datetime.datetime.strftime(
            datetime.datetime.fromisoformat(data['date_end']),
            "%d/%m/%y"
        )

        if data['auto_extend']:
            data['renewal_date'] = data['date_end']

        else:
            data['renewal_date'] = None
            data['next_payment_days'] = None

        data['payment_item_per_month'] = data['payment_per_period'] / length
        data['period_str'] = f"{data['interval_count']} {data['interval']}"
        data['payment_date'] = datetime.datetime.strftime(
            datetime.datetime.fromisoformat(data['payment_date']),
            "%d/%m/%y"
        )

        result.append(
            SubscriptionLast(
                **data
            )
        )
    return result


@router.post("/subscription/renew/{subscription_id}")
async def _renew_subscription_plan(subscription_id: int,
                                   duration: Literal['month', 'week', 'day'],
                                   duration_count: int,
                                   amount: int,
                                   db: AsyncSession = Depends(get_session),
                                   email: str = Depends(verifier)
                                   ):
    crud = CRUDService()

    subscription = await crud.get_by_field(db, Subscription, 'id', subscription_id, single=True)

    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    items = await get_subscription_items(db, subscription_id)

    cache = {}

    for item, proxy, modem in items:
        cache[item.stripe_item_id] = f'{modem.name} {duration_count} {duration}'

    new_plan = await update_subscription_plan(subscription.stripe_subscription_id, cache, duration,
                                              duration_count, amount, subscription.period_end)

    await crud.update_fields(db, Subscription, subscription.id, **{
        'period_start': convert_from_timestamp(new_plan.current_period_start),
        'period_end': convert_from_timestamp(new_plan.current_period_end),
        'trial_end': convert_from_timestamp(new_plan.trial_end),
        'payment_per_period': amount
    })

    return {
        'status': "successful"
    }


@router.delete('/subscription/customer/deleteItem/{subscription_id}/{item_id}')
async def _delete_subscription_item(subscription_id: int,
                                    item_id: int,
                                    email: str = Depends(verifier),
                                    db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    subscription = await crud.get_by_field(db, Subscription, 'id', subscription_id, single=True)

    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription Not found")

    subscription_item = await crud.get_by_field(db, SubscriptionItem, 'id', item_id, single=True)

    if subscription_item is None:
        raise HTTPException(status_code=404, detail="Subscription Item not found")

    try:
        deleted = await stripe_delete_item(
            subscription.stripe_subscription_id,
            subscription_item.stripe_item_id
        )
    except:
        deleted = await stripe_delete_subscription(subscription.stripe_subscription_id)
        await crud.update_fields(db, Subscription, subscription_id, **{
            'is_active': False,
            'period_end': datetime.datetime.now()
        })

    await crud.update_fields(db, SubscriptionItem, subscription_item.id, **{
        'is_active': False
    })

    return {
        "status": "successful"
    }


@router.get('/subscription/allCustomers/orders/list', dependencies=[Depends(admin_verifier)])
async def _get_all_users_orders(
        query_search: str = None,
        carrier: Literal['Verizon', 'ATT', 'T-MOBILE'] = None,
        payment_method: Literal['paypal', 'crypto', 'visa', 'mastercard'] = None,
        order_date_start: str = None,
        order_date_end: str = None,

        status: Literal['pending', 'success', 'failed'] = None,
        offset: int = 0,
        limit: int = 10,
        db: AsyncSession = Depends(get_session)) -> OrderInterfaceResponse:
    if order_date_start is not None:
        try:
            order_date_start = datetime.datetime.strptime(order_date_start, f'%d/%m/%y')
        except:
            raise HTTPException(status_code=422,
                                detail="Incorrect order_date_start. Must be format %d/%m/%y. Example: 01/07/24")
    if order_date_end is not None:
        try:
            order_date_end = datetime.datetime.strptime(order_date_end, f'%d/%m/%y')
        except:
            raise HTTPException(status_code=422,
                                detail="Incorrect order_date_end. Must be format %d/%m/%y. Example: 01/07/24")

    orders = await get_all_orders(db=db,
                                  status=status,
                                  query_search=query_search,
                                  carrier=carrier,
                                  payment_method=payment_method,
                                  order_date_start=order_date_start,
                                  order_date_end=order_date_end,
                                  )
    result = []

    for id_, payment_link, payment_service, first_name, last_name, email, \
            created, carrier, period_str, \
            amount, discount_code, discount_amount, \
            payment_method, status in orders[offset: offset + limit]:
        result.append(
            OrderInterface(
                order_id=id_,
                payment_link=payment_link,

                first_name=first_name,
                last_name=last_name,
                email=email,
                date_created=datetime.datetime.strftime(created, "%d/%m/%y"),
                carrier=carrier,
                amount=amount,
                period_str=period_str,
                discount_amount=discount_amount,
                discount_code=discount_code,
                payment_method=payment_method,
                status=status.value
            )
        )
    return OrderInterfaceResponse(
        total=len(orders),
        orders=result
    )

@router.get('/test')
async def _get_all_users_orders(
        session_id: str,
        db: AsyncSession = Depends(get_session)
):
    from models.stripe import Transaction
    crud = CRUDService()
    transaction = await crud.get_by_field(db, Transaction, 'created_local_session_id', session_id, single=True)

    if transaction:
        await crud.update_fields(db, Transaction, transaction.id, **{"status": "failed"})

    return {
        "status": "successful"
    }
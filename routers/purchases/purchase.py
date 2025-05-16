from fastapi import APIRouter, HTTPException, Depends
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from logic.authorization.validator import AdminVerifier, TokenVerifier

from crud.balance import get_purchases_balance, get_closest_payments, get_last_payments, get_count_purchases

from scheme.purchases import PurchasesBalance, ClosestPayments, LastPayment, ClosestPaymentsResponse

admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter()


@router.get("/purchases/balance")
async def _get_purchases(email: str = Depends(verifier),
                         db: AsyncSession = Depends(get_session)) -> PurchasesBalance:

    purchases = await get_count_purchases(db, email)

    try:
        data = await get_purchases_balance(db, email)
        payment, crypto_balance, = data[0]

    except IndexError as e:
        payment, crypto_balance = 0, 0
    except Exception as e:
        raise e
    scheme = PurchasesBalance(
        total_payment_per_month=payment or 0,
        crypto_balance=crypto_balance or 0,
        total_purchases=purchases or 0
    )

    return scheme


@router.get("/purchases/closest_payments")
async def _get_closest_payments(email: str = Depends(verifier),
                                offset: int = 0,
                                limit: int = 5,
                                db: AsyncSession = Depends(get_session)) -> ClosestPaymentsResponse:
    result = []
    data = await get_closest_payments(db, email)

    if not len(data):
        raise HTTPException(status_code=404, detail="Payments not found")

    for i in data[offset: offset + limit]:
        subscription_id, days_left, subscription_item_id, carrier, location = i
        result.append(
            ClosestPayments(
                carrier_name=carrier,
                proxy_location=location,
                days_left=int(days_left),
                subscription_id=subscription_id,
                subscription_item_id=subscription_item_id
            )
        )
    return ClosestPaymentsResponse(
        total=len(data),
        payments=result
    )


@router.get('/purchases/last_payment')
async def _get_last_payment(email: str = Depends(verifier),
                            db: AsyncSession = Depends(get_session)) -> LastPayment:
    data = await get_last_payments(db, email)
    if data is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    (order_id, sub_id, sub_active, sub_item_id,
     amount, created, carrier, location, http_ip, http_port,
     socks5_ip, socks5_port) = await get_last_payments(db, email)

    payment = LastPayment(
        order_id=order_id,
        carrier_name=carrier,
        proxy_location=location,
        http_ip=http_ip,
        http_port=http_port,
        socks5_ip=socks5_ip,
        socks5_port=socks5_port,
        date_payment=created,
        subscription_id=sub_id,
        subscription_item_id=sub_item_id,
        is_active=sub_active,
        amount=int(amount)
    )
    return payment


from typing import Literal, Optional

from fastapi import Depends, APIRouter
from fastapi.requests import Request
from fastapi.exceptions import HTTPException

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from config.settings import MAIN_HOST

from crud.base import CRUDService

from logic.authorization.validator import TokenVerifier
from logic.stripe.customer import client, create_params, create_customer, retrieve_customer
from logic.stripe.payment import create_price
from models.discounts import Discount
from models.stripe import StripeAccount, Transaction, TransactionOrder
from models.user import User
from models.proxies import Modem

router = APIRouter()

verifier = TokenVerifier()


@router.post("/create-checkout-session")
async def create_checkout_session(request: Request,
                                  proxy: Literal['Verizon', 'ATT', 'T-MOBILE'],
                                  duration: Literal['month', 'week', 'day'],
                                  duration_count: int,
                                  payment_method: Literal['Paypal', 'Card'],
                                  price: float,
                                  quantity: int,
                                  auto_extended: bool,
                                  discount: Optional[str] = None,
                                  location: Optional[str] = 'Germany',
                                  email: str = Depends(verifier),
                                  db: AsyncSession = Depends(get_session)
                                  ):
    crud = CRUDService()

    discount_id = None
    line_items = []

    if discount:
        discount = await crud.get_by_field(db, Discount, 'code', discount, single=True)
        discount_id = discount.id

    for i in range(quantity):
        price_object = await create_price(
            unit_amount=int(price * 100 // quantity),
            recurring={
                "interval": duration.lower(),
                "interval_count": duration_count,
            },
            product_data={"name": f"{proxy} {duration_count} {duration}"}
        )
        line_items.append({
            'price': price_object,
            'quantity': 1
        })

    user = await crud.get_by_field(db, User, "email", email, single=True)

    customer = await crud.get_by_field(db, StripeAccount, 'user_id', user.id, single=True)

    if customer is None:
        customer = await create_customer(f"{user.first_name} {user.last_name}", user.email)
        customer_db_id = await crud.create(db, StripeAccount, **{
            'user_id': user.id,
            'stripe': customer
        })
    else:
        customer_db_id = customer.id
        customer = customer.stripe

    customer_id = customer

    customer = await retrieve_customer(customer)

    uid = str(uuid.uuid4())

    carrier = await crud.get_by_field(db, Modem, 'name', proxy, single=True)

    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")

    payment_link = await client.checkout.sessions.create_async(create_params(
        payment_method_types=[payment_method.lower()],
        customer=customer,
        line_items=line_items,
        mode='subscription',
        saved_payment_method_options={"payment_method_save": "enabled"},
        subscription_data={'metadata': {
            'local_uid': uid,
            'auto_extended': auto_extended,
            'local_discount_id': discount_id,
            'location': location,
            'carrier_id': carrier.id,
            'user_id': user.id
        }},
        success_url=f'{MAIN_HOST}/webhook/success?customer={customer_id}&payment_id={str(uid)}&extend={auto_extended}',
        cancel_url=f'{MAIN_HOST}/webhook/cancel?customer={customer_id}&payment_id={str(uid)}&extend={auto_extended}',
    ))

    transaction = {
        'uid': uid,
        'user_stripe_id': customer_db_id,
        'invoice_stripe_id': None,
        'created_local_session_id': payment_link.id,
        'amount': price,
        'status': 'pending'
    }

    try:
        transaction_id = await crud.create(db, Transaction, **transaction)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error while creating transaction")

    await crud.create(db, TransactionOrder, **{
        'transaction_id': transaction_id,
        'modem_id': carrier.id,
        'period_str': f'{duration_count} {duration}',
        'discount_id': discount_id,
        'payment_method': payment_method.lower(),
        'payment_link': payment_link.url,
    })

    return payment_link.url

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
from logic.crypto.crypto_cloud import create_invoice
from logic.stripe.customer import client, create_params, create_customer, retrieve_customer
from logic.stripe.payment import create_price
from logic.crypto.main import create_crypto_payment

from models.discounts import Discount
from models.stripe import StripeAccount, Transaction, TransactionOrder, TransactionService
from models.user import User
from models.proxies import Modem

router = APIRouter()

verifier = TokenVerifier()


@router.post("/create-crypto-checkout-session")
async def create_crypto_checkout_session(request: Request,
                                         proxy: Literal['Verizon', 'ATT', 'T-MOBILE'],
                                         duration: Literal['month', 'week', 'day'],
                                         duration_count: int,
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
        if discount:
            discount_id = discount.id

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

    uid = str(uuid.uuid4())

    carrier = await crud.get_by_field(db, Modem, 'name', proxy, single=True)

    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")

    try:
        payment_link, payment_id = await create_crypto_payment(
            name=f"{proxy}",
            description=f"{proxy} {duration_count} {duration_count}",
            amount=price,
            metadata={
                "subscription": {
                    'local_uid': uid,
                    'auto_extended': auto_extended,
                    'local_discount_id': discount_id,
                    'location': location,
                    'carrier_id': carrier.id,
                    'user_id': user.id,
                    'line_items': line_items.copy()
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while creating crypto payment link. Error - {str(e)}")

    transaction = {
        'uid': uid,
        'user_stripe_id': customer_db_id,
        'invoice_stripe_id': None,
        'created_local_session_id': payment_id,
        'amount': price,
        'status': 'pending',
        "service": TransactionService.coinbase
    }
    try:
        transaction_id = await crud.create(db, Transaction, **transaction)
        await crud.create(db, TransactionOrder, **{
            'transaction_id': transaction_id,
            'modem_id': carrier.id,
            'period_str': f'{duration_count} {duration}',
            'discount_id': discount_id,
            'payment_method': 'crypto',
            'payment_link': payment_link,
            "quantity": quantity,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while creating transaction - {str(e)}")

    return payment_link


@router.post("/create-crypto-cloud-checkout-session")
async def create_crypto_checkout_session(request: Request,
                                         proxy: Literal['Verizon', 'ATT', 'T-MOBILE'],
                                         duration: Literal['month', 'week', 'day'],
                                         duration_count: int,
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
        if discount:
            discount_id = discount.id

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

    uid = str(uuid.uuid4())

    #carrier = await crud.get_by_field(db, Modem, 'name', proxy, single=True)
    carrier = await crud.get_one(db, Modem, 1)
    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")

    try:
        payment_link, payment_id = await create_invoice(
            amount=price,
            metadata={
                "subscription": {
                    'local_uid': uid,
                    'auto_extended': auto_extended,
                    'local_discount_id': discount_id,
                    'location': location,
                    'carrier_id': carrier.id,
                    'user_id': user.id,
                    'line_items': line_items.copy()
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while creating crypto cloud payment link. Error - {str(e)}")

    transaction = {
        'uid': uid,
        'user_stripe_id': customer_db_id,
        'invoice_stripe_id': None,
        'created_local_session_id': payment_id,
        'amount': price,
        'status': 'pending',
        "service": TransactionService.crypto_cloud
    }
    try:
        transaction_id = await crud.create(db, Transaction, **transaction)
        await crud.create(db, TransactionOrder, **{
            'transaction_id': transaction_id,
            'modem_id': carrier.id,
            'period_str': f'{duration_count} {duration}',
            'discount_id': discount_id,
            'payment_method': 'crypto',
            'payment_link': payment_link,
            "quantity": quantity,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while creating transaction - {str(e)}")

    return payment_link

# @router.post("/create-crypto-balance-session")
# async def create_crypto_balance_checkout_session(request: Request,
#                                                  amount: float,
#                                                  email: str = Depends(verifier),
#                                                  db: AsyncSession = Depends(get_session)
#                                                  ):
#     crud = CRUDService()
#
#     user = await crud.get_by_field(db, User, "email", email, single=True)
#
#     customer = await crud.get_by_field(db, StripeAccount, 'user_id', user.id, single=True)
#
#     if customer is None:
#         customer = await create_customer(f"{user.first_name} {user.last_name}", user.email)
#         customer_db_id = await crud.create(db, StripeAccount, **{
#             'user_id': user.id,
#             'stripe': customer
#         })
#     else:
#         customer_db_id = customer.id
#
#     uid = str(uuid.uuid4())
#
#     try:
#         payment_link, payment_id = await create_crypto_payment(
#             name=f"Add Balance",
#             description=f"Add Balance amount: {amount}",
#             amount=amount,
#             metadata={
#                 "balance": {
#                     'local_uid': uid,
#                     'user_id': user.id,
#                 }
#             }
#         )
#     except:
#         raise HTTPException(status_code=500, detail="Error while creating crypto payment link")
#
#     transaction = {
#         'uid': uid,
#         'user_stripe_id': customer_db_id,
#         'invoice_stripe_id': None,
#         'created_local_session_id': payment_link,
#         'amount': amount,
#         'status': 'pending',
#         "service": "coinbase"
#     }
#     try:
#         await crud.create(db, Transaction, **transaction)
#     except:
#         raise HTTPException(status_code=500, detail="Error while creating transaction")
#     return payment_link

import stripe
from fastapi import APIRouter, Depends

from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse, JSONResponse

from config.database import get_session
from config.settings import (
    WEBHOOK_SECRET,
    FRONT_HOST,
    FRONT_SUCCESS_URL,
    FRONT_CANCEL_URL,
)
from logic.stripe.webhooks import actions_update_subscription, actions_create_subscription, actions_delete_subscription

from models.stripe import (
    Transaction,
    Subscription,
    StripeAccount,
    SubscriptionCharge,
)
from models.user import User

from crud.base import CRUDService


from logic.stripe.main import client

router = APIRouter()

endpoint_secret = WEBHOOK_SECRET


@router.get('/webhook/success')
async def webhook_success(
        request: Request,
        customer: str | None = None,
        payment_id: str | int | None = None,
        extend: str | int | None = None,
        db: AsyncSession = Depends(get_session)
):
    response = RedirectResponse(FRONT_SUCCESS_URL)

    response.headers["Location"] = FRONT_SUCCESS_URL
    response.headers["Access-Control-Allow-Credentials"] = "true"

    response.status_code = status.HTTP_308_PERMANENT_REDIRECT

    for key, value in request.cookies.items():
        response.set_cookie(key, value)

    request.cookies['secure'] = 'true'
    response.session = request.session

    return response


@router.get('/webhook/cancel')
async def webhook_cancel(
        request: Request,
        customer: str | int | None = None,
        payment_id: str | int | None = None,
        extend: str | int | None = None,
        db: AsyncSession = Depends(get_session)
):

    response = RedirectResponse(FRONT_CANCEL_URL)

    response.headers["Location"] = FRONT_CANCEL_URL
    response.headers["Access-Control-Allow-Credentials"] = "true"

    response.status_code = status.HTTP_308_PERMANENT_REDIRECT

    for key, value in request.cookies.items():
        response.set_cookie(key, value)

    request.cookies['secure'] = 'true'
    response.session = request.session

    return response


@router.post('/webhook/subscription')
async def webhook_subscription(request: Request, db: AsyncSession = Depends(get_session)):
    event = None
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    crud = CRUDService()

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e
    try:
        subscription = getattr(event.data.object, 'subscription', None)
        subscription_stripe = None
        subscription_db = None
        if subscription is None and event['type'] != 'checkout.session.expired':
            raise HTTPException(status_code=404, detail="Subscription from other Service")

        if subscription:
            subscription_db = await crud.get_by_field(db, Subscription, 'stripe_subscription_id', subscription, single=True)

            subscription_stripe = await client.subscriptions.retrieve_async(subscription)

        customer = await crud.get_by_field(db, StripeAccount, 'stripe', event.data.object.customer, single=True)
        if not customer:
            raise HTTPException(status_code=422, detail=f"Wrong customer (other Service)")

        user = await crud.get_by_field(db, User, 'id', customer.user_id, single=True)

        if event['type'] == 'invoice.payment_succeeded':
            default_plan = {
                "interval": "day",
                "interval_count": 1
            }

            plan = subscription_stripe.get('items', {}).get('data', [{'plan': default_plan}])[0]['plan']
            try:
                if not subscription_db:
                    transaction_id, subscription_id = await actions_create_subscription(
                        event=event,
                        subscription_stripe=subscription_stripe,
                        customer=customer,
                        plan=plan,
                        db=db
                    )

                else:
                    transaction_id, subscription_id = await actions_update_subscription(
                        event=event,
                        subscription_stripe=subscription_stripe,
                        subscription_db=subscription_db,
                        user=user,
                        customer=customer,
                        plan=default_plan,
                        db=db
                    )

                await crud.create(db, SubscriptionCharge, **{
                    'transaction_id': transaction_id,
                    'subscription_id': subscription_id,
                    'interval': plan['interval'],
                    'interval_count': plan['interval_count']
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"CRITICAL Error while handling webhook. {e}")

        elif event['type'] == 'customer.subscription.deleted':
            await actions_delete_subscription(
                subscription_db=subscription_db,
                user=user,
                db=db
            )
        elif event['type'] == 'checkout.session.expired':
            session_id = event.data.object['id']

            transaction = await crud.get_by_field(db, Transaction, 'created_local_session_id', session_id, single=True)

            if transaction:
                await crud.update_fields(db, Transaction, transaction.id, **{"status": "failed"})

        else:
            print('Unhandled event type {}'.format(event['type']))
    except HTTPException as e:
        return JSONResponse(
            status_code=200,
            content={
                "detail": e.detail,
                "status_code_original": e.status_code,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"UNCAUGHT CRITICAL ERROR: {e}")

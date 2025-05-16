import stripe

from logic.stripe.main import client
from logic.stripe.customer import create_params


async def create_price(unit_amount: int, recurring: dict, product_data: dict, currency: str = 'usd'):
    params = create_params(unit_amount=unit_amount, recurring=recurring, product_data=product_data, currency=currency)
    data = await client.prices.create_async(params)
    return data.stripe_id


async def get_payment_by_invoice(invoice):
    try:
        invoice = await client.invoices.retrieve_async(invoice)
        payment_intent = await client.payment_intents.retrieve_async(invoice.payment_intent)
        payment_method = await client.payment_methods.retrieve_async(payment_intent.payment_method)

        if payment_method['type'] == 'card':
            card = payment_method.card
            payment_data = {
                'method': 'card',
                'payment_data': {
                    'brand': card.brand,
                    'exp_month': card.exp_month,
                    'exp_year': card.exp_year,
                    'last4': card.last4
                }
            }
        else:
            payment_data = {
                'method': 'paypal',
                'payment_data': None
            }
    except:
        payment_data = {
            'method': "unknown",
            'payment_data': None
        }
    return payment_data


async def create_payment_intent(customer_id: str, amount: int, currency: str = 'usd'):
    params = create_params(customer=customer_id,
                           setup_future_usage='off_session',
                           amount=amount,
                           currency=currency,
                           payment_method_types=[
                               'card'
                           ]
                           )
    try:
        intent = await client.payment_intents.create_async(params)
    except stripe.error.StripeError as e:
        return {
            'error': e.user_message,
            'status_code': 400
        }
    except Exception as e:
        return {
            'error': str(e),
            'status_code': 400
        }

    return intent.client_secret

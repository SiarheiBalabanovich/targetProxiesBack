from logic.stripe.customer import create_params
from logic.stripe.main import client
from logic.stripe.payment import create_price
from stripe._subscription import Subscription as StripeSubscription
from datetime import datetime
from datetime import timedelta
async def create_line_items(quantity: int, price: float, modem_name: str, duration: str, duration_count: int, ):
    line_items = []
    for i in range(quantity):
        price_object = await create_price(
            unit_amount=int(price * 100 // quantity),
            recurring={
                "interval": duration.lower(),
                "interval_count": duration_count,
            },
            product_data={"name": f"{modem_name} {duration_count} {duration}"}
        )
        line_items.append({
            'price': price_object,
            'quantity': 1
        })
    return line_items


async def create_subscription_stripe_script_logic(
        customer_id: str,
        quantity: int,
        price: float,
        modem_name: str,
        duration: str,
        duration_count: int,
        cancel_at_period_end: bool = True,
        **kwargs,
) -> StripeSubscription:
    def calculate_trial(duration, duration_count) -> int:
        now = datetime.now()
        time = 60 * 60 * 24 #1 day
        if duration == 'day':
            time = time * duration_count
        elif duration == 'week':
            time = (time * 7) * duration
        else:
            time = (time * 30) * duration_count
        time_end = int((now + timedelta(seconds=time)).timestamp())
        return time_end

    line_items = await create_line_items(
        quantity=quantity,
        price=price,
        modem_name=modem_name,
        duration=duration,
        duration_count=duration_count,
    )
    params = create_params(
        customer=customer_id,
        items=line_items,
        cancel_at_period_end=cancel_at_period_end,
        trial_end=calculate_trial(duration, duration_count)
    )
    subscription = client.subscriptions.create(
        params=params
    )
    return subscription


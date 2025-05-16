from logic.stripe.main import client
from logic.stripe.payment import create_price, create_params


async def update_subscription_plan(subscription_stripe_id: str,
                                   items: dict,
                                   interval,
                                   interval_count,
                                   amount,
                                   current_period_end):
    new_items = []
    old_items = []

    for item_id, product_data in items.items():
        price_object = await create_price(
            unit_amount=int(amount * 100),
            recurring={
                "interval": interval.lower(),
                "interval_count": interval_count,
            },
            product_data={'name': product_data})

        new_items.append({
            'price': price_object
        })
        old_items.append(
            {
                'id': item_id,
                'deleted': True
            }
        )

    modified = await client.subscriptions.update_async(
        subscription_stripe_id,
        create_params(
            **{
                'items': [
                    *old_items,
                    *new_items,
                ]

            }
        ),

    )
    return modified


async def stripe_delete_item(subscription_stripe_id, item_stripe_id):
    modified = await client.subscriptions.update_async(
        subscription_stripe_id,
        create_params(
            **{
                'items': [
                    {
                        'id': item_stripe_id,
                        'deleted': True
                    }
                ],
            }
        ),

    )
    return modified


async def stripe_delete_subscription(subscription_stripe_id):
    deleted = await client.subscriptions.cancel_async(subscription_stripe_id)
    return deleted

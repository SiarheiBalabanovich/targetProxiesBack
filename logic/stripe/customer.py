from logic.stripe.main import client


def create_params(**kwargs):
    return client.customers.CreateParams(**kwargs)


async def create_customer(name, email):
    params = create_params(name=name, email=email)

    try:
        response = await client.customers.create_async(params)
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
    return response.id


async def retrieve_customer(customer_id):
    try:
        customer = await client.customers.retrieve_async(customer_id)
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
    return customer

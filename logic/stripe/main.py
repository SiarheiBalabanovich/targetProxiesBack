from stripe import StripeClient
from config.settings import STRIPE_SECRET


client = StripeClient(STRIPE_SECRET)


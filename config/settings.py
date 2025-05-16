import os

from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv(BASE_DIR / '.env') is False:
    raise AssertionError(f"File .env not found, search directory: {BASE_DIR / '.env'}")

load_dotenv()

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'whsec_908314fab7469451141c501fa493f4ace5e05c4e0b0c78d65013d4259af40111')
CRYPTO_API_KEY = os.getenv('CRYPTO_API_KEY', '')

MAIN_HOST = os.getenv("MAIN_HOST", "http://127.0.0.1:8000")
GOOGLE_CALLBACK = "google-auth"

FRONT_HOST = os.getenv("FRONT_HOST", "http://127.0.0.1:8000")
FRONT_CANCEL_URL = FRONT_HOST + "/dashboard#purchase"
FRONT_SUCCESS_URL = FRONT_HOST + "/dashboard"
FRONT_REDIRECT_GOOGLE = FRONT_HOST #+ '/test'
FRONT_FORGET_PASSWORD_URL = FRONT_HOST + "/new-password"

SECRET_KEY_SESSION = os.getenv("SECRET_KEY_SESSION", "smthing")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "1"))


SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
ALGORITHM_JWT = os.getenv("ALGORITHM_JWT")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
ACCESS_TOKEN_SAVE_SESSION_MINUTES = int(os.getenv("ACCESS_TOKEN_SAVE_SESSION_MINUTES", "10080"))

EMAIL = os.getenv("EMAIL", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_password")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))

CLIENT_ID = os.getenv("CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "your_client_secret")

USER_DEFAULT_PASSWORD = os.getenv("USER_DEFAULT_PASSWORD", "test")

STRIPE_SECRET = os.getenv("STRIPE_SECRET", "sk_test_51HzpNoF0PE5pJujat0tYdGLA3dpeFfzyuABf9wDkict37Qiw9Kd81S6yrobTgQDLgKKgPjBkvqUVOyyySxf3YuuQ00Ds4wmSm5")

GOOGLE_REDIRECT_URL = f"{MAIN_HOST}/auth/google/handle"
GOOGLE_REDIRECT_LINK = f"https://accounts.google.com/o/oauth2/auth?client_id={CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URL}&response_type=code&scope=openid email profile"

STRIPE_PAYMENT_URL = 'https://checkout.stripe.com/c/pay'
CRYPTO_PAYMENT_URL = 'https://commerce.coinbase.com/pay'
CRYPTO_CLOUD_PAYMENT_URL = 'https://pay.cryptocloud.plus'

CRYPTO_CLOUD_API_KEY = os.getenv("CRYPTO_CLOUD_API_KEY", "")
CRYPTO_CLOUD_SHOP_ID = os.getenv("CRYPTO_CLOUD_SHOP_ID", "")
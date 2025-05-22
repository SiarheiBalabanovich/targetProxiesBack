import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from queue import Queue
from contextlib import asynccontextmanager

from logging.handlers import QueueHandler, QueueListener
from logging import StreamHandler, getLogger

from config.logging_conf import setup_logging
from config.settings import CLIENT_ID

from routers.users.user import router as UserRouter
from routers.users.password import router as PasswordRouter
from routers.users.auth import router as AuthRouter
from routers.stripe.webhook import router as WBRouter
from routers.stripe.payment import router as PaymentRouter
from routers.discounts.discount import router as DiscountRouter
from routers.purchases.purchase import router as PurchaseRouter
from routers.stripe.subscription import router as SubscriptionRouter
from routers.proxies.proxy import router as ProxyRouter
from routers.docs.doc import router as APIIntegrationRouter
from routers.stats.stat import router as StatRouter
from routers.pages.pages import router as PagesRouter
from routers.graphics.graphic import router as GraphicRouter
from routers.crypto.payment import router as CryptoRouter
from routers.notifies.notify import router as NotifyRouter

logger = getLogger(__name__)
setup_logging(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    que = Queue()

    logger.addHandler(QueueHandler(que))

    listener = QueueListener(que, StreamHandler())
    listener.start()
    logger.debug(f'Logger has started')

    yield

    logger.debug(f"Logger has stopped")

    listener.stop()


# app = FastAPI(lifespan=lifespan)
app = FastAPI(lifespan=lifespan, redirect_slashes=False)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "https://d3b0gjqgkudb0o.cloudfront.net",
    "https://app.targetedproxies-dev.com",
    'http://localhost:5173'
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

app.add_middleware(SessionMiddleware, secret_key=CLIENT_ID)

api_router = APIRouter(prefix="/api")

api_router.include_router(UserRouter,     prefix="/users",        tags=["User"])
api_router.include_router(PasswordRouter, prefix="/password",     tags=["Password"])
api_router.include_router(AuthRouter,     prefix="/auth",         tags=["Auth"])
api_router.include_router(WBRouter,       prefix="/webhook",      tags=["Webhook"])
api_router.include_router(DiscountRouter, prefix="/discount",     tags=["Discount"])
api_router.include_router(PaymentRouter,  prefix="/payment",      tags=["Payment"])
api_router.include_router(PurchaseRouter, prefix="/purchase",     tags=["Purchases"])
api_router.include_router(SubscriptionRouter, prefix="/subscription", tags=["Subscription"])
api_router.include_router(ProxyRouter,    prefix="/proxy",        tags=["Proxies"])
api_router.include_router(StatRouter,     prefix="/stat",         tags=["AdminPanel"])
api_router.include_router(PagesRouter,    prefix="/pages",        tags=["Pages"])
api_router.include_router(GraphicRouter,  prefix="/graphic",      tags=["Graphics"])
api_router.include_router(CryptoRouter,   prefix="/crypto",       tags=["Crypto"])
api_router.include_router(NotifyRouter,   prefix="/notify",       tags=["Notifies"])


app.include_router(api_router)

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import uvicorn

    print("=== REGISTERED ROUTES ===")
    for route in app.routes:
        print(f"{route.path:30} -> {route.methods}")
    print("=========================")

    uvicorn.run(app, host="0.0.0.0", port=8000)
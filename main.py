import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
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

app.include_router(UserRouter, tags=["User"])
app.include_router(PasswordRouter, tags=["Password"])
app.include_router(AuthRouter, tags=["Auth"])
app.include_router(WBRouter, tags=["Webhook"])
app.include_router(DiscountRouter, tags=["Discount"])
app.include_router(PaymentRouter, tags=["Payment"])
app.include_router(PurchaseRouter, tags=['Purchases'])
app.include_router(SubscriptionRouter, tags=['Subscription'])
app.include_router(ProxyRouter, tags=["Proxies"])
#app.include_router(APIIntegrationRouter, tags=["Integration"])
app.include_router(StatRouter, tags=['AdminPanel'])
app.include_router(PagesRouter, tags=['Pages'])
app.include_router(GraphicRouter, tags=['Graphics'])
app.include_router(CryptoRouter, tags=['Crypto'])
app.include_router(NotifyRouter, tags=['Notifies'])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
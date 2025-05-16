from sqlalchemy import (
    Column, Integer, String,
    DateTime, Float, Boolean,
    Enum, JSON
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql import func

from config.database import Base
from models.discounts import Discount

from models.user import User
from models.proxies import Proxy, Modem

import enum


class TransactionStatus(str, enum.Enum):
    success = "success"
    pending = "pending"
    failed = "failed"


class PaymentMethod(enum.Enum):
    paypal = "paypal"
    card = "card"
    crypto = "crypto"
    unknown = 'unknown'


class TransactionService(str, enum.Enum):
    stripe = "stripe"
    coinbase = "coinbase"
    crypto_cloud = "crypto_cloud"


class SubscriptionAction(str, enum.Enum):
    bought = "bought"
    prolong = "prolong"


class StripeAccount(Base):
    __tablename__ = 'stripe_account'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), unique=True)
    stripe = Column(String, unique=True)

    user = relationship(User, back_populates="user_stripe")
    subscription = relationship('Subscription', back_populates='stripe_account')


class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    invoice_stripe_id = Column(String, unique=True, nullable=True)
    service = Column(Enum(TransactionService), server_default='stripe')
    created_local_session_id = Column(String, unique=True, nullable=True)
    uid = Column(String, unique=True)

    user_stripe_id = Column(Integer, ForeignKey(StripeAccount.id, ondelete='CASCADE'))

    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now())

    amount = Column(Float)
    status = Column(Enum(TransactionStatus))

    user_stripe = relationship(StripeAccount)
    transaction_order = relationship('TransactionOrder', back_populates='transaction', uselist=False)


class TransactionOrder(Base):
    __tablename__ = 'transaction_orders'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id, ondelete='CASCADE'))
    modem_id = Column(Integer, ForeignKey(Modem.id, ondelete="SET NULL"), nullable=True)
    period_str = Column(String)
    discount_id = Column(Integer, ForeignKey(Discount.id, ondelete="SET NULL"), nullable=True)
    payment_method = Column(String, nullable=True)
    payment_link = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    discount = relationship(Discount)
    modem = relationship(Modem)
    transaction = relationship(Transaction, back_populates="transaction_order", uselist=False)


class Subscription(Base):
    __tablename__ = 'subscription'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    date_start = Column(DateTime(timezone=True))
    date_end = Column(DateTime(timezone=True), nullable=True)

    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    period_str = Column(String)

    trial_end = Column(DateTime(timezone=True), nullable=True)

    stripe_account_id = Column(Integer, ForeignKey(StripeAccount.id, ondelete="CASCADE"))
    stripe_subscription_id = Column(String, unique=True)
    discount_id = Column(Integer, ForeignKey(Discount.id, ondelete="SET NULL"))

    payment_per_period = Column(Float, default=50.0)

    auto_extend = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)

    stripe_account = relationship('StripeAccount', back_populates='subscription')
    items = relationship('SubscriptionItem', back_populates='subscription')
    payment = relationship('SubscriptionPaymentData', back_populates="subscription")
    charges = relationship('SubscriptionCharge', back_populates='subscription')
    discount = relationship('Discount')


class SubscriptionCharge(Base):
    __tablename__ = 'subscription_charge'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id, ondelete='SET NULL'), unique=True)
    subscription_id = Column(Integer, ForeignKey(Subscription.id, ondelete="SET NULL"))

    interval = Column(String, default='day')
    interval_count = Column(Integer, default=1)

    transaction = relationship(Transaction)
    subscription = relationship(Subscription, back_populates='charges')


class SubscriptionPaymentData(Base):
    __tablename__ = "subscription_payment_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    subscription_id = Column(Integer, ForeignKey(Subscription.id, ondelete="CASCADE"), unique=True)
    method = Column(Enum(PaymentMethod))
    payment_data = Column(JSON, nullable=True)

    subscription = relationship('Subscription', back_populates="payment")


class SubscriptionItem(Base):
    __tablename__ = "subscription_item"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey(Subscription.id, ondelete="CASCADE"))

    proxy_id = Column(Integer, ForeignKey(Proxy.id, ondelete='SET NULL'), unique=True)

    is_active = Column(Boolean, default=True)
    stripe_item_id = Column(String, unique=True)

    proxy = relationship('Proxy')
    subscription = relationship('Subscription', back_populates='items')

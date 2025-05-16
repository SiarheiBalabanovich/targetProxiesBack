from fastapi import APIRouter, Depends


from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal, List

from config.database import get_session

from crud.graphics import get_revenue, get_survey, get_sales_location, get_sales_carrier, get_revenue_source, \
    get_sales_customer

from scheme.graphics import GraphicInterface, GraphicMultiInterfaceCarrier, \
    GraphicMultiInterfacePayment

from logic.authorization.validator import AdminVerifier, TokenVerifier
from logic.utils.time import convert_str_month, convert_day_of_this_week
from logic.utils.graphic import insert_graphic, insert_graphic_dict, insert_graphic_enum

admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter()


@router.get('/graphics/revenue', dependencies=[Depends(admin_verifier)])
async def _get_revenue(period: Literal["month", "year", "week"],
                       db: AsyncSession = Depends(get_session)) -> List[GraphicInterface]:
    result = []

    data = await get_revenue(db, period)

    if period in ('month', 'year'):
        func = convert_str_month
    else:
        func = convert_day_of_this_week

    data = insert_graphic(data, period, 1, 2)

    for amount, name in data:
        result.append(
            GraphicInterface(
                name=func(name),
                amount=amount
            )
        )
    return result


@router.get('/graphics/survey', dependencies=[Depends(admin_verifier)])
async def _get_survey(period: Literal["month", "year", "week"],
                      db: AsyncSession = Depends(get_session)) -> List[GraphicInterface]:
    data = await get_survey(db, period)

    if not len(data):
        return []

    result = []

    for name, percent in data:
        result.append(
            GraphicInterface(
                name=name,
                amount=int(percent)
            )
        )
    return result


@router.get('/graphics/location', dependencies=[Depends(admin_verifier)])
async def _get_location(period: Literal["month", "year", "week"],
                        db: AsyncSession = Depends(get_session)) -> List[GraphicInterface]:
    data = await get_sales_location(db, period)

    if not len(data):
        return []

    result = []

    for name, amount in data:
        result.append(
            GraphicInterface(
                name=name,
                amount=int(amount)
            )
        )
    return result


@router.get('/graphics/salesCarrier', dependencies=[Depends(admin_verifier)])
async def _get_sales_carrier(period: Literal["month", "year", "week"],
                             db: AsyncSession = Depends(get_session)) -> List[GraphicMultiInterfaceCarrier]:
    data = await get_sales_carrier(db, period)

    data = insert_graphic_dict(data, period, ['T-MOBILE', 'ATT', 'Verizon'])

    result = []

    if period in ('month', 'year'):
        func = convert_str_month
    else:
        func = convert_day_of_this_week

    for pr, tmobile, att, verizon in data:
        result.append(
            GraphicMultiInterfaceCarrier(
                name=func(pr),
                tMobile=tmobile,
                att=att,
                verizon=verizon
            )
        )
    return result


@router.get('/graphics/revenueSource', dependencies=[Depends(admin_verifier)])
async def _get_revenue_source(period: Literal["month", "year", "week"],
                              db: AsyncSession = Depends(get_session)) -> List[GraphicMultiInterfacePayment]:
    data = await get_revenue_source(db, period)

    keys = ['paypal', 'card', 'crypto']

    data = insert_graphic_enum(data, period, keys)
    result = []

    if period in ('month', 'year'):
        func = convert_str_month
    else:
        func = convert_day_of_this_week

    for pr, paypal, card, crypto in data:
        result.append(
            GraphicMultiInterfacePayment(
                name=func(pr),
                paypal=paypal,
                creditCard=card,
                crypto=crypto
            )
        )
    return result


@router.get('/graphics/salesCustomer', dependencies=[Depends(admin_verifier)])
async def _get_sales_customer(period: Literal["month", "year", "week"],
                              db: AsyncSession = Depends(get_session)) -> List[GraphicInterface]:
    data = await get_sales_customer(db, period)

    if not len(data):
        return []

    result = []

    for name, amount in data:
        result.append(
            GraphicInterface(
                name=name,
                amount=amount
            )
        )

    return result

import datetime
from typing import Literal
from pytz import timezone

zone = timezone('utc')


def convert_from_timestamp(timestamp):
    try:
        return datetime.datetime.fromtimestamp(timestamp, tz=zone)
    except:
        return None


def last_day_of_month():
    today = datetime.datetime.now()
    next_month = today.replace(day=28) + datetime.timedelta(days=4)

    last_day = next_month - datetime.timedelta(days=next_month.day)
    last_day = last_day.replace(hour=23, minute=59, second=59)
    return last_day



def convert_str_day(day):
    return {
        1: "MON",
        2: "TUE",
        3: "WED",
        4: "THU",
        5: "FRI",
        6: "SAT",
        7: "SUN"
    }.get(day)


def convert_str_month(month):
    return {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec"
    }.get(month)


def convert_day_of_this_week(day):
    today = datetime.datetime.now()
    day = today.replace(day=day)

    day_str = day.isoweekday()
    return convert_str_day(day_str)


async def convert_period_to_timestamp(period: Literal['month', 'week', 'day'], period_count: int):
    now = datetime.datetime.utcnow()
    match period:
        case 'month':
            days = 30
        case 'week':
            days = 7
        case _:
            days = 1

    expire = (now + datetime.timedelta(days=days * period_count)).timestamp() #timestamp in milliseconds
    return int(expire * 1000) #timestamp in seconds

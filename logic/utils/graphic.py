from collections import defaultdict


def insert_graphic(source_data, period, date_index, values_length=2) -> list:
    total = 7 if period == 'week' else 12

    dates_have = [i[date_index] for i in source_data]

    values = [0 for _ in range(values_length)]

    result = []

    elem_have = 0
    for i in range(1, total + 1):
        if i in dates_have:
            result.append(
                source_data[elem_have]
            )
            elem_have += 1

        else:
            values_temp = values[:]
            values_temp[date_index] = i

            result.append(
                values_temp[:]
            )
    return result


def insert_graphic_dict(source_data: list, period: str, keys: list):
    group = defaultdict(dict)
    total = 7 if period == 'week' else 12

    for row in source_data:
        modem, amount, day = row

        if not group[day].get(modem):
            group[day][modem] = amount
        else:
            group[day][modem] += amount

    result = []
    for i in range(1, total + 1):
        data = group.get(i, {})

        result.append(
            (i, *tuple(data.get(i, 0.0) for i in keys))
        )
    return result


def insert_graphic_enum(source_data: list, period: str, keys: list):
    group = defaultdict(dict)
    total = 7 if period == 'week' else 12

    for row in source_data:
        card, amount, day = row

        card = card.value

        if not group[day].get(card):
            group[day][card] = amount
        else:
            group[day][card] += amount

    result = []
    for i in range(1, total + 1):
        data = group.get(i, {})

        result.append(
            (i, *tuple(data.get(i, 0.0) for i in keys))
        )
    return result

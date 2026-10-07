import calendar
from datetime import date

import holidays

MALAY_DAYS = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]
STATES = sorted(code for code in holidays.Malaysia.subdivisions_aliases if len(code) == 3 and code.isupper())


def public_holidays(config, year):
    return holidays.Malaysia(subdiv=config.state, years=year)


def in_training(config, d):
    return config.start_date <= d <= config.end_date


def parse_days(spec):
    result = set()
    for part in filter(None, (p.strip() for p in spec.split(","))):
        start, dash, end = part.partition("-")
        if not start.isdigit() or (dash and not end.isdigit()):
            raise ValueError(f"'{spec}' isn't a list of days like 7-11,15")
        first, last = int(start), int(end or start)
        if not 1 <= first <= last <= 31:
            raise ValueError(f"'{spec}' isn't a list of days like 7-11,15")
        result.update(range(first, last + 1))
    return result


def working_days(year, month, config, skip=(), work=()):
    holidays_this_year = public_holidays(config, year)
    result = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        d = date(year, month, day)
        if not in_training(config, d):
            continue
        normal = d.weekday() < 5 and d not in holidays_this_year
        if (normal and day not in skip) or day in work:
            result.append(d)
    return result


def malay_day_name(d):
    return MALAY_DAYS[d.weekday()]


def long_date(d):
    return f"{d.day} {calendar.month_name[d.month]} {d.year}"

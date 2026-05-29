from datetime import date, datetime, timedelta


def parse_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def add_months(d, months):
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(d.day, 28))


def last_day_of_month(year, month):
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def period_to_dates(period, custom_start=None, custom_end=None):
    today = date.today()
    if period == "This month":
        start = today.replace(day=1)
        end = today
    elif period == "Last month":
        first = today.replace(day=1)
        end = first - timedelta(days=1)
        start = end.replace(day=1)
    elif period == "Last 3 months":
        start = add_months(today, -3)
        end = today
    elif period == "This year":
        start = today.replace(month=1, day=1)
        end = today
    elif period == "All time":
        start = date(2000, 1, 1)
        end = today
    elif period == "Custom range" and custom_start and custom_end:
        start = parse_date(custom_start)
        end = parse_date(custom_end)
    else:
        start = today.replace(day=1)
        end = today
    return start.isoformat(), end.isoformat()

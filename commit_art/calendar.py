from __future__ import annotations

from datetime import date, timedelta


def same_day_previous_year(today: date) -> date:
    try:
        return today.replace(year=today.year - 1)
    except ValueError:
        return today.replace(year=today.year - 1, day=28)


def previous_sunday(day: date) -> date:
    # Python: Monday is 0, Sunday is 6.
    days_since_sunday = (day.weekday() + 1) % 7
    return day - timedelta(days=days_since_sunday)


def first_contribution_day(today: date) -> date:
    return previous_sunday(same_day_previous_year(today))


def first_contribution_day_for_year(year: int) -> date:
    return previous_sunday(date(year, 1, 1))

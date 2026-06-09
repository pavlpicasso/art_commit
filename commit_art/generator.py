from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from commit_art.calendar import first_contribution_day, first_contribution_day_for_year
from commit_art.map_parser import MAP_COLUMNS, MAP_ROWS, commit_count_for_cell, validate_commit_map


@dataclass(frozen=True)
class PlannedCommitDay:
    day: date
    count: int


def generate_plan(
    commit_map: list[str],
    levels: dict[str, int],
    today: date | None = None,
    year: int | None = None,
) -> list[PlannedCommitDay]:
    validate_commit_map(commit_map, levels)

    if today is not None and year is not None:
        raise ValueError("Use either today or year, not both.")

    current = first_contribution_day_for_year(year) if year is not None else first_contribution_day(today or date.today())
    planned: list[PlannedCommitDay] = []

    for offset in range(MAP_ROWS * MAP_COLUMNS):
        week = offset // MAP_ROWS
        weekday = offset % MAP_ROWS
        count = commit_count_for_cell(commit_map[weekday][week], levels)
        if count:
            planned.append(PlannedCommitDay(day=current, count=count))
        current += timedelta(days=1)

    return planned


def iter_commit_datetimes(
    plan: list[PlannedCommitDay],
    timezone: str,
    commit_hour: int,
) -> list[datetime]:
    values: list[datetime] = []
    for item in plan:
        for minute in range(item.count):
            values.append(datetime(item.day.year, item.day.month, item.day.day, commit_hour, minute))
    return values


def summarize_plan(plan: list[PlannedCommitDay]) -> tuple[int, int]:
    return len(plan), sum(item.count for item in plan)

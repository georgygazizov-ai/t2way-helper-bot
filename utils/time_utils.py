from datetime import datetime, time
from zoneinfo import ZoneInfo


# Все временные метки в БД храним в UTC в формате SQLite:
# YYYY-MM-DD HH:MM:SS
UTC = ZoneInfo("UTC")
DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_utc_str() -> str:
    """
    Текущее время в UTC в формате строки для БД и сравнений.
    """

    return datetime.now(UTC).strftime(DT_FORMAT)


def reminder_utc_str_for_date(date_str: str, timezone_name: str) -> str | None:
    """
    Возвращает UTC-строку для 09:00 по Москве в дату тренинга.

    Если этот момент уже прошёл, возвращает None:
    напоминание создавать бессмысленно.
    """

    tz = ZoneInfo(timezone_name)

    training_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    local_dt = datetime.combine(training_date, time(9, 0), tzinfo=tz)
    utc_dt = local_dt.astimezone(UTC)

    if utc_dt <= datetime.now(UTC):
        return None

    return utc_dt.strftime(DT_FORMAT)


def today_str_in_tz(timezone_name: str) -> str:
    """
    Текущая дата в указанном часовом поясе в формате YYYY-MM-DD.
    """

    return datetime.now(ZoneInfo(timezone_name)).strftime("%Y-%m-%d")
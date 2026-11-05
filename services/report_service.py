from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv
from pathlib import Path

from repositories.report_repo import ReportRepo
from services.training_service import format_lead_name


PERIOD_DAYS = {
    "days_30": 30,
    "days_90": 90,
    "days_180": 180,
    "days_365": 365,
}

PERIOD_TITLES = {
    "days_30": "последние 30 дней",
    "days_90": "последние 90 дней",
    "days_180": "последние 180 дней",
    "days_365": "последние 365 дней",
}

REPORT_TITLES = {
    "leads": "Статистика по амбассадорам (проведённые тренинги)",
    "cities": "Статистика по городам",
    "macro": "Статистика по макрорегионам",
    "months": "Статистика по месяцам",
    "formats": "Статистика по форматам",
}


def resolve_period(
    period_key: str,
    timezone_name: str,
    start: str | None = None,
    end: str | None = None,
) -> tuple[str | None, str | None]:
    """
    Превращает ключ периода в границы дат YYYY-MM-DD.

    Возвращает (None, None) для периода «всё время».
    """

    if period_key == "all":
        return None, None

    if period_key == "custom":
        return start, end

    days = PERIOD_DAYS.get(period_key)

    if days is None:
        return None, None

    today = datetime.now(ZoneInfo(timezone_name)).date()
    start_date = today - timedelta(days=days - 1)

    return start_date.isoformat(), today.isoformat()


def describe_period(
    period_key: str,
    start_date: str | None,
    end_date: str | None,
) -> str:
    """
    Человекочитаемое описание периода.
    """

    if start_date is None:
        return "Период: всё время"

    if period_key == "custom":
        return f"Период: с {start_date} по {end_date}"

    return f"Период: {PERIOD_TITLES.get(period_key, period_key)}"


async def build_text_report(
    report_repo: ReportRepo,
    kind: str,
    period_key: str,
    timezone_name: str,
    start: str | None = None,
    end: str | None = None,
) -> str:
    """
    Собирает текстовый отчёт выбранного среза за выбранный период.
    """

    start_date, end_date = resolve_period(period_key, timezone_name, start, end)
    period_title = describe_period(period_key, start_date, end_date)

    total = await report_repo.total_conducted(start_date, end_date)

    if kind == "leads":
        rows = await report_repo.by_lead(start_date, end_date)
        lines = [f"{format_lead_name(row)}: {row['cnt']}" for row in rows]
    elif kind == "cities":
        rows = await report_repo.by_city(start_date, end_date)
        lines = [f"{row['name']}: {row['cnt']}" for row in rows]
    elif kind == "macro":
        rows = await report_repo.by_macro_region(start_date, end_date)
        lines = [f"{row['name']}: {row['cnt']}" for row in rows]
    elif kind == "months":
        rows = await report_repo.by_month(start_date, end_date)
        lines = [f"{row['month']}: {row['cnt']}" for row in rows]
    elif kind == "formats":
        rows = await report_repo.by_format(start_date, end_date)
        lines = [f"{row['name']}: {row['cnt']}" for row in rows]
    else:
        return f"Неизвестный срез: {kind}"

    header = (
        f"{REPORT_TITLES.get(kind, kind)}\n"
        f"{period_title}\n"
        f"Всего проведено тренингов: {total}\n"
    )

    if not lines:
        return header + "\nДанных за период нет."

    numbered = "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))

    return header + "\n" + numbered

def build_annual_csv(rows, year: str, out_dir: Path) -> Path:
    """
    Формирует годовой отчёт в CSV (Windows-формат):
    - разделитель «;» (открывается в Excel без мастеров импорта);
    - кодировка UTF-8 с BOM (кириллица читается корректно);
    - переводы строк CRLF.

    Столбцы: №, Амбассадор, Должность, Кол-во проведенных программ за N.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"annual_report_{year}.csv"

    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";", lineterminator="\r\n")

        writer.writerow(
            ["№", "Амбассадор", "Должность", f"Кол-во проведенных программ за {year}"]
        )

        for index, row in enumerate(rows, 1):
            writer.writerow(
                [
                    index,
                    format_lead_name(row),
                    row["position"] or "",
                    row["cnt"],
                ]
            )

    return path

def format_month_label(month: str) -> str:
    """
    Превращает метку месяца из БД в формат ММ.ГГ.
    Пример: 2026-01 -> 01.26
    """

    try:
        year, mon = month.split("-")
        return f"{mon}.{year[2:]}"
    except ValueError:
        return month


def format_short_name(row) -> str:
    """
    Короткое имя для графиков: Фамилия И.О.
    Пример: Иванов И.И.
    """

    last_name = row["last_name"] or ""

    initials = ""
    if row["first_name"]:
        initials += f"{row['first_name'][0]}."
    if row["patronymic"]:
        initials += f"{row['patronymic'][0]}."

    return f"{last_name} {initials}".strip()
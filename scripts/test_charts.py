import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio

from database.connection import Database
from repositories.report_repo import ReportRepo
from services.report_service import (
    build_annual_csv,
    format_month_label,
    format_short_name,
)
from utils.charts import bar_chart, line_chart, pie_chart


async def main():
    db = Database(Path("data/t2way.sqlite3"))
    await db.connect()

    repo = ReportRepo(db)

    # Столбчатая: по амбассадорам (Фамилия И.О.)
    rows = await repo.by_lead()
    items = [(format_short_name(r), r["cnt"]) for r in rows]
    print("создан:", bar_chart(items, "Статистика по амбассадорам", "chart_leads.png"))

    # Столбчатая: по городам
    rows = await repo.by_city()
    items = [(r["name"], r["cnt"]) for r in rows]
    print("создан:", bar_chart(items, "Статистика по городам", "chart_cities.png"))

    # Столбчатая: по макрорегионам
    rows = await repo.by_macro_region()
    items = [(r["name"], r["cnt"]) for r in rows]
    print("создан:", bar_chart(items, "Статистика по макрорегионам", "chart_macro.png"))

    # Круговая: по форматам
    rows = await repo.by_format()
    items = [(r["name"], r["cnt"]) for r in rows]
    print("создан:", pie_chart(items, "Статистика по форматам тренингов", "chart_formats.png"))

    # Линейный: по месяцам (ММ.ГГ)
    rows = await repo.by_month()
    items = [(format_month_label(r["month"]), r["cnt"]) for r in rows]
    print("создан:", line_chart(items, "Динамика тренингов по месяцам", "chart_months.png"))

    # Годовой отчёт в CSV (полные ФИО)
    years = await repo.get_conducted_years()
    print("доступные годы:", years)

    if years:
        year = years[0]
        rows = await repo.annual_by_lead(year)
        path = build_annual_csv(rows, year, Path("data/reports"))
        print("создан:", path)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь поиска,
# чтобы скрипт работал из любой папки.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import Database
from repositories.report_repo import ReportRepo
from services.report_service import build_text_report


async def main():
    db = Database(Path("data/t2way.sqlite3"))
    await db.connect()

    repo = ReportRepo(db)

    for kind in ("leads", "cities", "macro", "months", "formats"):
        text = await build_text_report(repo, kind, "all", "Europe/Moscow")
        print("\n" + text)
        print("-" * 50)

    text = await build_text_report(repo, "leads", "days_30", "Europe/Moscow")
    print("\n" + text)
    print("-" * 50)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
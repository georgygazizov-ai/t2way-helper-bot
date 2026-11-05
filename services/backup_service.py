import asyncio
import logging
import sqlite3
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from database.connection import Database


logger = logging.getLogger(__name__)

BACKUP_PREFIX = "t2way_backup_"
RETENTION_DAYS = 30


def _check_and_zip(tmp_path: Path, zip_path: Path) -> bool:
    """
    Синхронная часть: проверка целостности копии и упаковка в ZIP.
    Выполняется в отдельном потоке, чтобы не блокировать бота.
    """

    con = sqlite3.connect(tmp_path)
    check = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()

    if check != "ok":
        return False

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(tmp_path, arcname="t2way.sqlite3")

    # Проверяем, что сам ZIP не повреждён.
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            return False

    return True


async def create_backup(
    db: Database,
    backup_dir: Path,
    timezone_name: str,
) -> Path | None:
    """
    Создаёт резервную копию БД:
    1. Консистентная копия через VACUUM INTO.
    2. Проверка целостности копии.
    3. Упаковка в ZIP и удаление временной копии.
    """

    backup_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(ZoneInfo(timezone_name)).replace(tzinfo=None)
    stamp = now.strftime("%Y-%m-%d_%H-%M")

    tmp_path = backup_dir / f"tmp_{stamp}.sqlite3"
    zip_path = backup_dir / f"{BACKUP_PREFIX}{stamp}.zip"

    # Консистентная копия без остановки бота.
    await db.execute(f"VACUUM INTO '{tmp_path}'")

    ok = await asyncio.to_thread(_check_and_zip, tmp_path, zip_path)

    tmp_path.unlink(missing_ok=True)

    if not ok:
        logger.error(
            "[ERROR] Резервная копия %s не прошла проверку целостности",
            zip_path.name,
        )
        zip_path.unlink(missing_ok=True)
        return None

    logger.info(
        "[SYSTEM] Создан бэкап: %s (%s КБ)",
        zip_path.name,
        zip_path.stat().st_size // 1024,
    )

    return zip_path


def cleanup_old_backups(
    backup_dir: Path,
    now: datetime,
    days: int = RETENTION_DAYS,
) -> int:
    """
    Удаляет бэкапы старше указанного количества дней.
    """

    cutoff = now - timedelta(days=days)
    removed = 0

    for path in backup_dir.glob(f"{BACKUP_PREFIX}*.zip"):
        try:
            stamp = path.name[len(BACKUP_PREFIX):-len(".zip")]
            created = datetime.strptime(stamp, "%Y-%m-%d_%H-%M")
        except ValueError:
            continue

        if created < cutoff:
            path.unlink(missing_ok=True)
            removed += 1

    if removed:
        logger.info("[SYSTEM] Удалено старых бэкапов: %s", removed)

    return removed


def has_backup_for_date(backup_dir: Path, date_str: str) -> bool:
    """
    Проверяет, есть ли бэкап за указанную дату (YYYY-MM-DD).
    """

    return any(backup_dir.glob(f"{BACKUP_PREFIX}{date_str}_*.zip"))
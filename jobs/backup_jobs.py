import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from database.connection import Database
from services.backup_service import (
    cleanup_old_backups,
    create_backup,
    has_backup_for_date,
)
from utils.time_utils import today_str_in_tz


logger = logging.getLogger(__name__)


async def daily_backup_job(db: Database, settings) -> None:
    """
    Ежедневная задача: создать бэкап и почистить старые.
    """

    now = datetime.now(ZoneInfo(settings.timezone)).replace(tzinfo=None)

    path = await create_backup(db, settings.backup_dir, settings.timezone)

    if path is not None:
        cleanup_old_backups(settings.backup_dir, now)


async def backup_if_missing(db: Database, settings) -> None:
    """
    При старте бота создаёт бэкап, если за сегодня его ещё нет.
    Защищает от простоя в момент 00:00.
    """

    today = today_str_in_tz(settings.timezone)

    if not has_backup_for_date(settings.backup_dir, today):
        logger.info("[SYSTEM] Бэкап за сегодня отсутствует — создаём при старте")
        await daily_backup_job(db, settings)


def register_backup_jobs(scheduler, db: Database, settings) -> None:
    """
    Регистрирует ежедневную задачу бэкапа в 00:00 МСК.
    """

    scheduler.add_job(
        func=daily_backup_job,
        trigger="cron",
        hour=0,
        minute=0,
        kwargs={"db": db, "settings": settings},
        id="daily_backup",
        name="Ежедневный бэкап базы данных",
        max_instances=1,
        replace_existing=True,
    )

    logger.info("[SYSTEM] Задача бэкапа зарегистрирована (ежедневно 00:00 МСК)")
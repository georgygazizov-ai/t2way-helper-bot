import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo


logger = logging.getLogger(__name__)


def create_scheduler(timezone_name: str) -> AsyncIOScheduler:
    """
    Создаёт асинхронный планировщик задач.

    Все задачи будут работать в указанном часовом поясе
    (у нас Europe/Moscow).
    """

    scheduler = AsyncIOScheduler(timezone=ZoneInfo(timezone_name))

    logger.info(
        "[SYSTEM] Планировщик создан (часовой пояс: %s)",
        timezone_name,
    )

    return scheduler
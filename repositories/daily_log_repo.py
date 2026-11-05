import logging

from database.connection import Database


logger = logging.getLogger(__name__)


class DailyLogRepo:
    """
    Журнал ежедневных событий.
    Защищает от повторной отправки поздравлений и других дневных задач.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def is_done(self, event_type: str, event_date: str) -> bool:
        """
        Возвращает True, если событие за эту дату уже выполнено.
        """

        query = """
            SELECT 1 AS x
            FROM daily_events_log
            WHERE event_type = ?
              AND event_date = ?
        """

        row = await self.db.fetchone(query, (event_type, event_date))

        return row is not None

    async def mark_done(self, event_type: str, event_date: str, sent_at: str) -> None:
        """
        Помечает событие выполненным за дату.
        """

        query = """
            INSERT OR IGNORE INTO daily_events_log (event_type, event_date, sent_at)
            VALUES (?, ?, ?)
        """

        await self.db.execute(query, (event_type, event_date, sent_at))
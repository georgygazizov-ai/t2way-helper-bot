import logging

from database.connection import Database


logger = logging.getLogger(__name__)


class ReminderRepo:
    """
    Репозиторий напоминаний о тренингах.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        training_id: int,
        user_id: int,
        reminder_type: str,
        scheduled_for: str,
    ) -> None:
        """
        Создаёт напоминание.
        INSERT OR IGNORE защищает от дублей благодаря UNIQUE в схеме.
        """

        query = """
            INSERT OR IGNORE INTO reminders
                (training_id, user_id, reminder_type, scheduled_for)
            VALUES (?, ?, ?, ?)
        """

        await self.db.execute(query, (training_id, user_id, reminder_type, scheduled_for))

    async def get_due(self, now_utc: str) -> list:
        """
        Возвращает напоминания, которые пора отправить.
        """

        query = """
            SELECT *
            FROM reminders
            WHERE is_sent = 0
              AND scheduled_for <= ?
            ORDER BY scheduled_for
        """

        return await self.db.fetchall(query, (now_utc,))

    async def mark_sent(self, reminder_id: int, sent_at: str) -> None:
        """
        Помечает напоминание отправленным.
        """

        query = """
            UPDATE reminders
            SET is_sent = 1, sent_at = ?
            WHERE id = ?
        """

        await self.db.execute(query, (sent_at, reminder_id))

    async def delete_unsent_for_training(self, training_id: int) -> int:
        """
        Удаляет все неотправленные напоминания тренинга.
        Используется при отмене и переносе тренинга.
        """

        count_query = """
            SELECT COUNT(*) AS cnt
            FROM reminders
            WHERE training_id = ?
              AND is_sent = 0
        """

        row = await self.db.fetchone(count_query, (training_id,))
        count = int(row["cnt"]) if row else 0

        query = """
            DELETE FROM reminders
            WHERE training_id = ?
              AND is_sent = 0
        """

        await self.db.execute(query, (training_id,))

        if count:
            logger.info(
                "[DB] Удалено %s неотправленных напоминаний тренинга %s",
                count,
                training_id,
            )

        return count

    async def mark_overdue_as_sent(self, now_utc: str) -> int:
        """
        Помечает просроченные напоминания отправленными без реальной отправки.

        Используется при старте бота: напоминания, пропущенные
        во время простоя, не отправляются задним числом.
        """

        count_query = """
            SELECT COUNT(*) AS cnt
            FROM reminders
            WHERE is_sent = 0
              AND scheduled_for < ?
        """

        row = await self.db.fetchone(count_query, (now_utc,))
        count = int(row["cnt"]) if row else 0

        if count:
            query = """
                UPDATE reminders
                SET is_sent = 1
                WHERE is_sent = 0
                  AND scheduled_for < ?
            """

            await self.db.execute(query, (now_utc,))

        return count
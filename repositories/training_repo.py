import logging

from database.connection import Database

logger = logging.getLogger(__name__)


class TrainingRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        date: str,
        format_type: str,
        city_id: int,
        created_by: int,
    ) -> int:
        """Создает новый тренинг и возвращает его ID."""
        query = """
            INSERT INTO trainings (date, format, city_id, status, created_by)
            VALUES (?, ?, ?, 'assigned', ?)
        """
        await self.db.execute(query, (date, format_type, city_id, created_by))
        
        row = await self.db.fetchone("SELECT last_insert_rowid()")
        return row[0]

    async def assign_lead(self, training_id: int, user_id: int) -> None:
        """Назначает ведущего на тренинг."""
        query = """
            INSERT INTO training_leads (training_id, user_id)
            VALUES (?, ?)
        """
        await self.db.execute(query, (training_id, user_id))

    async def get_by_id(self, training_id: int):
        """Возвращает тренинг по ID."""
        query = "SELECT * FROM trainings WHERE id = ?"
        return await self.db.fetchone(query, (training_id,))

    async def get_leads(self, training_id: int) -> list:
        """Возвращает список ведущих тренинга."""
        query = """
            SELECT u.user_id, u.first_name, u.last_name, u.patronymic
            FROM training_leads tl
            JOIN users u ON tl.user_id = u.user_id
            WHERE tl.training_id = ?
            ORDER BY u.last_name, u.first_name
        """
        return await self.db.fetchall(query, (training_id,))

    async def get_all_trainings(self, status_filter: str | None = None):
        """Возвращает все тренинги с возможностью фильтрации по статусу."""
        query = "SELECT * FROM trainings"
        params = ()

        if status_filter:
            query += " WHERE status = ?"
            params = (status_filter,)

        query += " ORDER BY date DESC"

        return await self.db.fetchall(query, params)

    async def update_training(
        self,
        training_id: int,
        date: str | None = None,
        format_type: str | None = None,
        city_id: int | None = None,
    ) -> None:
        """Обновляет поля тренинга."""
        updates = []
        params = []

        if date is not None:
            updates.append("date = ?")
            params.append(date)

        if format_type is not None:
            updates.append("format = ?")
            params.append(format_type)

        if city_id is not None:
            updates.append("city_id = ?")
            params.append(city_id)

        if not updates:
            return

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(training_id)

        query = f"UPDATE trainings SET {', '.join(updates)} WHERE id = ?"
        await self.db.execute(query, tuple(params))

        logger.info("[AUDIT] Обновлен тренинг %s", training_id)

    async def remove_all_leads(self, training_id: int) -> None:
        """Удаляет всех ведущих тренинга."""
        query = "DELETE FROM training_leads WHERE training_id = ?"
        await self.db.execute(query, (training_id,))
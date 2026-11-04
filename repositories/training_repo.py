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
import logging
from database.connection import Database
from database.models import City

logger = logging.getLogger(__name__)


class CityRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _row_to_model(self, row) -> City | None:
        if row is None:
            return None
        return City(
            id=row["id"],
            name=row["name"],
            macro_region_id=row["macro_region_id"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_all_active(self) -> list[City]:
        """Возвращает список всех активных городов."""
        query = "SELECT * FROM cities WHERE is_active = 1 ORDER BY name"
        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def create(self, name: str, macro_region_id: int) -> int:
        """Создает новый город и возвращает его ID."""
        query = "INSERT INTO cities (name, macro_region_id) VALUES (?, ?)"
        await self.db.execute(query, (name, macro_region_id))
        
        row = await self.db.fetchone("SELECT last_insert_rowid()")
        return row[0]

    async def deactivate(self, city_id: int) -> None:
        """Деактивирует город."""
        query = """
            UPDATE cities
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        await self.db.execute(query, (city_id,))
        logger.info("[DB] Город %s деактивирован", city_id)

    async def get_by_id(self, city_id: int) -> City | None:
        """
        Возвращает город по ID.
        """

        query = "SELECT * FROM cities WHERE id = ?"
        row = await self.db.fetchone(query, (city_id,))

        return self._row_to_model(row)

    async def get_active_by_macro_region(self, macro_region_id: int) -> list[City]:
        """
        Возвращает активные города выбранного макрорегиона.
        """

        query = """
            SELECT *
            FROM cities
            WHERE is_active = 1
              AND macro_region_id = ?
            ORDER BY name
        """

        rows = await self.db.fetchall(query, (macro_region_id,))
        return [self._row_to_model(row) for row in rows]
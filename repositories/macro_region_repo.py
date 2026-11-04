import logging
from database.connection import Database
from database.models import MacroRegion

logger = logging.getLogger(__name__)


class MacroRegionRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _row_to_model(self, row) -> MacroRegion | None:
        """Преобразует сырую строку из БД в модель."""
        if row is None:
            return None
        return MacroRegion(
            id=row["id"],
            name=row["name"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_all_active(self) -> list[MacroRegion]:
        """Возвращает список всех активных макрорегионов."""
        query = "SELECT * FROM macro_regions WHERE is_active = 1 ORDER BY name"
        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def create(self, name: str) -> int:
        """Создает новый макрорегион и возвращает его ID."""
        query = "INSERT INTO macro_regions (name) VALUES (?)"
        await self.db.execute(query, (name,))
        
        row = await self.db.fetchone("SELECT last_insert_rowid()")
        return row[0]

    async def deactivate(self, region_id: int) -> None:
        """Деактивирует макрорегион (не удаляет физически)."""
        query = """
            UPDATE macro_regions
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        await self.db.execute(query, (region_id,))
        logger.info("[DB] Макрорегион %s деактивирован", region_id)
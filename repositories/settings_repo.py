import logging

from database.connection import Database

logger = logging.getLogger(__name__)

class SettingsRepo:
    """
    Репозиторий для хранения настроек приложения в БД.
    Используется для динамических значений, которые можно менять через бота.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get(self, key: str, default: str | None = None) -> str | None:
        """Возвращает значение настройки по ключу."""
        query = "SELECT value FROM app_settings WHERE key = ?"
        row = await self.db.fetchone(query, (key,))
        if row is None:
            return default
        return row["value"]

    async def set(self, key: str, value: str) -> None:
        """Создаёт или обновляет настройку."""
        query = """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """
        await self.db.execute(query, (key, value))
        logger.info("[SETTINGS] Настройка %s обновлена", key)
from pathlib import Path
import logging

from database.connection import Database


logger = logging.getLogger(__name__)


DEFAULT_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


async def migrate_database(db: Database) -> None:
    """
    Лёгкие миграции для уже существующей базы данных.
    """

    rows = await db.fetchall("PRAGMA table_info(users)")
    columns = {row["name"] for row in rows}

    if "chat_id" not in columns:
        await db.execute("ALTER TABLE users ADD COLUMN chat_id INTEGER")
        logger.info("[DB] Миграция: добавлена колонка chat_id в таблицу users")


async def init_database(
    db: Database,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> None:
    """
    Создаёт таблицы и индексы, затем применяет миграции.
    """

    if not schema_path.exists():
        raise FileNotFoundError(f"Не найден файл схемы БД: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")

    await db.execute_script(schema_sql)
    await migrate_database(db)

    logger.info("[DB] Схема базы данных проверена и применена")
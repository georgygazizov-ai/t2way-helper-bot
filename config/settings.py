from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


# Корневая папка проекта.
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """
    Основные настройки проекта.

    Все настройки читаются из .env.
    Здесь держим только конфигурацию, без бизнес-логики.
    """

    bot_token: str
    root_user_ids: tuple[int, ...]
    common_chat_id: int | None

    app_env: str
    membership_mode: str
    timezone: str

    db_path: Path
    log_dir: Path
    backup_dir: Path

    delete_previous_bot_messages: bool
    max_file_size_mb: int
    broadcast_delay_seconds: float


def _parse_int_list(raw_value: str) -> tuple[int, ...]:
    """
    Преобразует строку вида '123,456,789' в кортеж чисел.
    Пустые значения игнорируются.
    """

    if not raw_value.strip():
        return ()

    result: list[int] = []

    for item in raw_value.split(","):
        item = item.strip()

        if not item:
            continue

        result.append(int(item))

    return tuple(result)


def _parse_optional_int(raw_value: str) -> int | None:
    """
    Преобразует строку в число.
    Если строка пустая, возвращает None.
    """

    value = raw_value.strip()

    if not value:
        return None

    return int(value)


def _parse_bool(raw_value: str) -> bool:
    """
    Простой парсер布尔-значений из .env.
    """

    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on", "да"}


def _resolve_path(raw_value: str) -> Path:
    """
    Если путь относительный, считаем его от корня проекта.
    Если абсолютный, используем как есть.
    """

    path = Path(raw_value)

    if path.is_absolute():
        return path

    return BASE_DIR / path


def load_settings() -> Settings:
    """
    Загружает настройки из .env.

    Важно:
    - токен бота обязателен;
    - root_user_ids обязательны;
    - common_chat_id пока может быть пустым.
    """

    load_dotenv(BASE_DIR / ".env")

    bot_token = os.getenv("MAX_BOT_TOKEN", "").strip()
    root_user_ids = _parse_int_list(os.getenv("ROOT_USER_IDS", ""))

    if not bot_token:
        raise ValueError("Не заполнен MAX_BOT_TOKEN в файле .env")

    if not root_user_ids:
        raise ValueError("Не заполнен ROOT_USER_IDS в файле .env")

    settings = Settings(
        bot_token=bot_token,
        root_user_ids=root_user_ids,
        common_chat_id=_parse_optional_int(os.getenv("COMMON_CHAT_ID", "")),

        app_env=os.getenv("APP_ENV", "development").strip(),
        membership_mode=os.getenv("MEMBERSHIP_MODE", "dev_always_true").strip(),
        timezone=os.getenv("TIMEZONE", "Europe/Moscow").strip(),

        db_path=_resolve_path(os.getenv("DB_PATH", "data/t2way.sqlite3")),
        log_dir=_resolve_path(os.getenv("LOG_DIR", "logs")),
        backup_dir=_resolve_path(os.getenv("BACKUP_DIR", "backups")),

        delete_previous_bot_messages=_parse_bool(
            os.getenv("DELETE_PREVIOUS_BOT_MESSAGES", "true")
        ),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "15")),
        broadcast_delay_seconds=float(os.getenv("BROADCAST_DELAY_SECONDS", "0.5")),
    )

    return settings
import logging

from config.settings import Settings
from repositories.settings_repo import SettingsRepo


logger = logging.getLogger(__name__)


class MembershipService:
    """
    Сервис проверки участия пользователя в общем чате.
    В режиме разработки всегда возвращает True.
    """

    def __init__(self, settings: Settings, settings_repo: SettingsRepo | None = None) -> None:
        self.settings = settings
        self.settings_repo = settings_repo

    async def get_common_chat_id(self) -> int | None:
        """
        Возвращает ID общего чата.
        Приоритет: БД (если задано) → .env
        """
        # Сначала проверяем БД
        if self.settings_repo is not None:
            db_chat_id = await self.settings_repo.get("common_chat_id")
            if db_chat_id and db_chat_id.strip():
                try:
                    return int(db_chat_id)
                except ValueError:
                    pass

        # Если в БД нет, используем .env
        return self.settings.common_chat_id

    async def is_user_in_common_chat(self, user_id: int) -> bool:
        """
        Проверяет, состоит ли пользователь в общем чате.
        В режиме разработки всегда возвращает True.
        """

        if self.settings.membership_mode == "dev_always_true":
            return True

        chat_id = await self.get_common_chat_id()

        if chat_id is None:
            return True  # Если чат не настроен, пропускаем

        # Здесь будет реальная проверка через MAX API
        # Пока возвращаем True как заглушку
        return True
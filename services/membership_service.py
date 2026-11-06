import logging

from maxapi import Bot

from config.settings import Settings
from repositories.settings_repo import SettingsRepo

logger = logging.getLogger(__name__)


class MembershipService:
    """
    Сервис проверки участия пользователя в общем чате.
    В режиме разработки всегда возвращает True.
    """

    def __init__(
        self,
        settings: Settings,
        settings_repo: SettingsRepo | None = None,
        bot: Bot | None = None,
    ) -> None:
        self.settings = settings
        self.settings_repo = settings_repo
        self.bot = bot

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
        """

        # В режиме разработки всегда возвращаем True
        if self.settings.membership_mode == "dev_always_true":
            return True

        chat_id = await self.get_common_chat_id()

        if chat_id is None:
            logger.warning("[MEMBERSHIP] ID общего чата не задан. Проверка пропущена.")
            return True

        if self.bot is None:
            logger.error("[MEMBERSHIP] Bot не передан в MembershipService. Проверка невозможна.")
            return True

        # Реальная проверка через API: запросим участника чата
        try:
            member = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)

            # Если объект вернулся — пользователь в чате
            if member is not None:
                logger.debug(
                    "[MEMBERSHIP] Пользователь %s найден в чате %s",
                    user_id, chat_id,
                )
                return True

            return False

        except Exception as exc:
            # API вернуло ошибку — скорее всего пользователь не в чате
            # или у бота нет прав доступа к списку участников
            error_name = type(exc).__name__
            error_msg = str(exc)

            # Типичная ошибка maxapi при отсутствии пользователя в чате
            if "not found" in error_msg.lower() or "member" in error_msg.lower():
                logger.debug(
                    "[MEMBERSHIP] Пользователь %s НЕ найден в чате %s: %s",
                    user_id, chat_id, error_msg,
                )
                return False

            # Другие ошибки логируем, но не блокируем регистрацию
            logger.warning(
                "[MEMBERSHIP] Ошибка проверки пользователя %s в чате %s: [%s] %s. Разрешаем доступ.",
                user_id, chat_id, error_name, error_msg,
            )
            return True
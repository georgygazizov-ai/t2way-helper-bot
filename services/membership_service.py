import logging

from config.settings import Settings


logger = logging.getLogger(__name__)


class MembershipService:
    """
    Сервис проверки участия пользователя в общем чате.

    Сейчас используется заглушка.
    Реальная проверка будет добавлена в самом конце разработки.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def is_user_in_common_chat(self, user_id: int) -> bool:
        """
        Возвращает True, если пользователь считается участником общего чата.

        Режимы:
        - dev_always_true: всегда True, удобно для разработки.
        - другие режимы добавим позже.
        """

        if self.settings.membership_mode == "dev_always_true":
            logger.debug(
                "[MEMBERSHIP] Заглушка: пользователь %s считается участником чата",
                user_id,
            )
            return True

        # Позже здесь будет реальная проверка через MAX API
        # или локальный кэш участников общего чата.
        return True
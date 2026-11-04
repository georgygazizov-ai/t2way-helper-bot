import logging

from maxapi.filters.middleware import BaseMiddleware

from repositories.user_repo import UserRepo
from utils.event_helpers import answer_event, get_event_text, get_event_user_id


logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Проверяет, что пользователь зарегистрирован и активен.

    Исключения:
    - /start — нужен для регистрации;
    - /help и /ping — технические команды.
    """

    UNPROTECTED_COMMANDS = {"/start", "/help", "/ping"}

    def __init__(self, user_repo: UserRepo) -> None:
        self.user_repo = user_repo

    async def __call__(self, handler, event_object, data: dict):
        user_id = await get_event_user_id(event_object)

        # Если событие вообще не связано с пользователем, пропускаем дальше.
        # Например, служебные события чата.
        if user_id is None:
            await handler(event_object, data)
            return

        text = get_event_text(event_object)
        command = text.split()[0] if text else None

        # Разрешаем базовые команды без регистрации.
        if command in self.UNPROTECTED_COMMANDS:
            await handler(event_object, data)
            return

        user = await self.user_repo.get_by_id(user_id)

        if user is None:
            logger.warning(
                "[SECURITY] Доступ запрещён. Пользователь не зарегистрирован: %s",
                user_id,
            )
            await answer_event(event_object, "Сначала зарегистрируйтесь в боте: /start")
            return

        if user.status != "active":
            logger.warning(
                "[SECURITY] Доступ запрещён. Статус пользователя %s: %s",
                user_id,
                user.status,
            )
            await answer_event(
                event_object,
                "Ваш доступ ограничен. Обратитесь к администратору.",
            )
            return

        # Передаём пользователя дальше в обработчики через data.
        data["current_user"] = user
        await handler(event_object, data)
import logging

from maxapi.filters.middleware import BaseMiddleware

from utils.event_helpers import answer_event, get_event_text
from utils.permissions import ROLE_ROOT, is_admin


logger = logging.getLogger(__name__)


class RoleMiddleware(BaseMiddleware):
    """
    Проверяет права доступа:
    - команды /admin... — администратор и root;
    - команды /root... — только root;
    - callback payload spr: и prof: — администратор и root.
    """

    async def __call__(self, handler, event_object, data: dict):
        user = data.get("current_user")

        if user is None:
            await handler(event_object, data)
            return

        text = get_event_text(event_object)
        command = text.split()[0] if text else None

        callback = getattr(event_object, "callback", None)
        payload = getattr(callback, "payload", "") if callback else ""

        if command and command.startswith("/root"):
            if user.role != ROLE_ROOT:
                logger.warning(
                    "[SECURITY] Отказ доступа к root-команде %s для пользователя %s",
                    command,
                    user.user_id,
                )
                await answer_event(event_object, "Недостаточно прав.")
                return

        if command and command.startswith("/admin"):
            if not is_admin(user):
                logger.warning(
                    "[SECURITY] Отказ доступа к админ-команде %s для пользователя %s",
                    command,
                    user.user_id,
                )
                await answer_event(event_object, "Недостаточно прав.")
                return

        if payload.startswith(("spr:", "prof:", "roles:", "train:", "brd:")):
            if not is_admin(user):
                logger.warning(
                    "[SECURITY] Отказ доступа к админ-кнопке %s для пользователя %s",
                    payload,
                    user.user_id,
                )
                await answer_event(event_object, "Недостаточно прав.")
                return

        await handler(event_object, data)
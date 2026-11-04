import logging

from maxapi import Dispatcher
from maxapi.types import Command, MessageCreated

from repositories.user_repo import UserRepo
from services.membership_service import MembershipService
from utils.event_helpers import get_event_chat_id
from utils.permissions import ROLE_ROOT, ROLE_TRAINER


logger = logging.getLogger(__name__)


def register_start_handler(
    dp: Dispatcher,
    bot,
    user_repo: UserRepo,
    membership_service: MembershipService,
) -> None:
    """
    Регистрирует обработчик /start.
    """

    @dp.message_created(Command("start"))
    async def start_handler(event: MessageCreated) -> None:
        from_user = await event.fetch_from_user()

        if from_user is None:
            logger.warning("[SYSTEM] Не удалось получить пользователя из /start")
            return

        user_id = from_user.user_id
        chat_id = await get_event_chat_id(event)

        user = await user_repo.get_by_id(user_id)

        # Пользователь уже есть в базе.
        if user is not None:
            # Запоминаем актуальный ID личного диалога.
            if chat_id is not None and user.chat_id != chat_id:
                await user_repo.update_chat_id(user_id, chat_id)

            if user.status == "left_chat":
                await event.message.answer(
                    "Ваш доступ ограничен, так как вы вышли из общего чата.\n"
                    "Обратитесь к администратору."
                )
                return

            if user.role == ROLE_ROOT:
                await event.message.answer("Root-пользователь уже зарегистрирован.")
                return

            await event.message.answer("Вы уже зарегистрированы в боте.")
            return

        # Пользователя ещё нет в базе.
        in_chat = await membership_service.is_user_in_common_chat(user_id)

        if not in_chat:
            logger.warning(
                "[SECURITY] Отказ регистрации: пользователь %s не найден в общем чате",
                user_id,
            )

            await event.message.answer(
                "Вы не найдены в общем чате сообщества.\n"
                "Обратитесь к администратору."
            )
            return

        max_first_name = getattr(from_user, "first_name", None)
        max_last_name = getattr(from_user, "last_name", None)

        await user_repo.create(
            user_id=user_id,
            role=ROLE_TRAINER,
            status="active",
            first_name=max_first_name,
            last_name=max_last_name,
            chat_id=chat_id,
        )

        logger.info(
            "[AUDIT] Новая регистрация пользователя: %s",
            user_id,
        )

        await event.message.answer(
            "Регистрация прошла успешно.\n"
            "Администратор заполнит вашу карточку."
        )

        # Уведомляем администраторов и root о новой регистрации.
        admins = await user_repo.get_admins()

        for admin in admins:
            if admin.user_id == user_id:
                continue

            if admin.chat_id is None:
                logger.warning(
                    "[ERROR] У администратора %s нет диалога с ботом — уведомление не отправлено",
                    admin.user_id,
                )
                continue

            try:
                await bot.send_message(
                    chat_id=admin.chat_id,
                    text=(
                        "Новая регистрация в боте.\n\n"
                        f"ID пользователя: {user_id}\n"
                        "Заполните карточку нового пользователя."
                    ),
                )
            except Exception as exc:
                logger.warning(
                    "[ERROR] Не удалось отправить уведомление администратору %s: %r",
                    admin.user_id,
                    exc,
                )
import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from keyboards.admin import roles_kb
from repositories.user_repo import UserRepo
from services.profile_service import get_full_name
from states.admin_states import AdminRoleStates
from utils.permissions import ROLE_ADMIN, ROLE_ROOT, ROLE_TRAINER, role_title
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu


logger = logging.getLogger(__name__)


def register_roles_handlers(
    dp: Dispatcher,
    bot,
    user_repo: UserRepo,
) -> None:
    """
    Управление ролями пользователей: администратор и root.
    """

    async def send_role_screen(event, context: MemoryContext, user) -> None:
        """Показывает экран пользователя с кнопками смены роли."""

        text = (
            f"Пользователь: {get_full_name(user)} (ID {user.user_id})\n\n"
            f"Текущая роль: {role_title(user.role)}"
        )

        await send_menu(
            event,
            context,
            text,
            roles_kb.get_role_actions_kb(user),
        )

    def get_deny_reason(target, actor) -> str | None:
        """
        Возвращает причину отказа в смене роли или None, если менять можно.
        """

        if target is None:
            return "Пользователь не найден."

        if target.role == ROLE_ROOT:
            return "Роль root задаётся в конфигурации сервера и не меняется через бота."

        if target.user_id == actor.user_id:
            return "Нельзя изменить собственную роль."

        return None

    async def notify_role_change(user, old_role: str, new_role: str) -> None:
        """Уведомляет пользователя о смене роли."""

        if user.chat_id is None:
            logger.warning(
                "[ERROR] У пользователя %s нет диалога с ботом — уведомление о смене роли не отправлено",
                user.user_id,
            )
            return

        try:
            await bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "Ваша роль в боте изменена: "
                    f"{role_title(old_role)} → {role_title(new_role)}."
                ),
            )
        except Exception as exc:
            logger.warning(
                "[ERROR] Не удалось уведомить пользователя %s о смене роли: %r",
                user.user_id,
                exc,
            )

    # === МЕНЮ ===

    @dp.message_created(Command("admin_roles"))
    async def cmd_roles(event: MessageCreated, context: MemoryContext):
        await context.clear()

        await send_menu(
            event,
            context,
            "Управление ролями пользователей:",
            roles_kb.get_roles_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "roles:menu")
    async def cb_roles_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Управление ролями пользователей:",
            roles_kb.get_roles_menu_kb(),
        )

    # === ПОИСК ПОЛЬЗОВАТЕЛЯ ===

    @dp.message_callback(F.callback.payload == "roles:search")
    async def cb_roles_search(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.set_state(AdminRoleStates.waiting_last_name)

        await send_menu(
            event,
            context,
            "Введите фамилию или часть фамилии пользователя:",
            roles_kb.get_cancel_kb(),
        )

    @dp.message_created(AdminRoleStates.waiting_last_name, F.message.body.text)
    async def fsm_roles_search(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        query = event.message.body.text.strip()

        # Root в этом сценарии не показываем никому: его роль не меняется.
        users = await user_repo.search_by_last_name(query, include_root=False)

        await context.clear()

        if not users:
            await send_menu(
                event,
                context,
                "Пользователи не найдены.",
                roles_kb.get_roles_menu_kb(),
            )
            return

        await send_menu(
            event,
            context,
            "Найденные пользователи:",
            roles_kb.get_users_list_kb(users),
        )

    # === ЭКРАН ПОЛЬЗОВАТЕЛЯ ===

    @dp.message_callback(F.callback.payload.startswith("roles:user:"))
    async def cb_roles_user(
        event: MessageCallback,
        context: MemoryContext,
        current_user,
    ):
        target_user_id = int(event.callback.payload.split(":")[-1])
        target_user = await user_repo.get_by_id(target_user_id)

        await delete_callback_message(event)

        deny_reason = get_deny_reason(target_user, current_user)

        if deny_reason:
            await send_menu(
                event,
                context,
                deny_reason,
                roles_kb.get_roles_menu_kb(),
            )
            return

        await send_role_screen(event, context, target_user)

    # === СМЕНА РОЛИ ===

    @dp.message_callback(F.callback.payload.startswith("roles:make_admin:"))
    async def cb_make_admin(
        event: MessageCallback,
        context: MemoryContext,
        current_user,
    ):
        target_user_id = int(event.callback.payload.split(":")[-1])
        target_user = await user_repo.get_by_id(target_user_id)

        await delete_callback_message(event)

        deny_reason = get_deny_reason(target_user, current_user)

        if deny_reason:
            await send_menu(event, context, deny_reason, roles_kb.get_roles_menu_kb())
            return

        if target_user.role != ROLE_TRAINER:
            await send_role_screen(event, context, target_user)
            return

        await user_repo.update_role(target_user_id, ROLE_ADMIN)

        logger.info(
            "[AUDIT] Пользователь %s назначен администратором (кем: %s)",
            target_user_id,
            current_user.user_id,
        )

        updated_user = await user_repo.get_by_id(target_user_id)
        await notify_role_change(updated_user, ROLE_TRAINER, ROLE_ADMIN)

        await send_role_screen(event, context, updated_user)

    @dp.message_callback(F.callback.payload.startswith("roles:make_trainer:"))
    async def cb_make_trainer(
        event: MessageCallback,
        context: MemoryContext,
        current_user,
    ):
        target_user_id = int(event.callback.payload.split(":")[-1])
        target_user = await user_repo.get_by_id(target_user_id)

        await delete_callback_message(event)

        deny_reason = get_deny_reason(target_user, current_user)

        if deny_reason:
            await send_menu(event, context, deny_reason, roles_kb.get_roles_menu_kb())
            return

        if target_user.role != ROLE_ADMIN:
            await send_role_screen(event, context, target_user)
            return

        await user_repo.update_role(target_user_id, ROLE_TRAINER)

        logger.info(
            "[AUDIT] Пользователь %s понижен до тренера (кем: %s)",
            target_user_id,
            current_user.user_id,
        )

        updated_user = await user_repo.get_by_id(target_user_id)
        await notify_role_change(updated_user, ROLE_ADMIN, ROLE_TRAINER)

        await send_role_screen(event, context, updated_user)
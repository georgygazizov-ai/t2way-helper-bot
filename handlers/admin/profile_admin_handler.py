import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from handlers.admin.profile_admin_form_handler import start_edit_form
from keyboards.admin import profile_admin_kb
from repositories.city_repo import CityRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.user_repo import UserRepo
from states.admin_states import AdminProfileSearchStates
from utils.permissions import ROLE_ROOT, is_root
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu


logger = logging.getLogger(__name__)


def register_profile_admin_handlers(
    dp: Dispatcher,
    bot,
    user_repo: UserRepo,
    city_repo: CityRepo,
    macro_repo: MacroRegionRepo,
) -> None:
    """
    Админское меню профилей: списки, поиск, просмотр карточек.
    Сама форма редактирования находится в profile_admin_form_handler.py
    """

    @dp.message_created(Command("admin_profiles"))
    async def cmd_profiles(event: MessageCreated, context: MemoryContext):
        await context.clear()

        await send_menu(
            event,
            context,
            "Управление профилями пользователей:",
            profile_admin_kb.get_profile_admin_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "prof:menu")
    async def cb_profile_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Управление профилями пользователей:",
            profile_admin_kb.get_profile_admin_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "prof:incomplete")
    async def cb_incomplete_profiles(
        event: MessageCallback,
        context: MemoryContext,
        current_user,
    ):
        await delete_callback_message(event)

        users = await user_repo.get_incomplete_profiles(
            include_root=is_root(current_user),
        )

        if not users:
            await send_menu(
                event,
                context,
                "Незаполненных карточек нет.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        await send_menu(
            event,
            context,
            "Выберите пользователя для заполнения карточки:",
            profile_admin_kb.get_users_list_kb(users),
        )

    @dp.message_callback(F.callback.payload == "prof:search")
    async def cb_search_start(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.set_state(AdminProfileSearchStates.waiting_last_name)

        await send_menu(
            event,
            context,
            "Введите фамилию или часть фамилии пользователя:",
            profile_admin_kb.get_cancel_profile_form_kb(),
        )

    @dp.message_created(AdminProfileSearchStates.waiting_last_name, F.message.body.text)
    async def fsm_search_last_name(
        event: MessageCreated,
        context: MemoryContext,
        current_user,
    ):
        await clear_last_bot_message(context)

        query = event.message.body.text.strip()

        users = await user_repo.search_by_last_name(
            query,
            include_root=is_root(current_user),
        )

        await context.clear()

        if not users:
            await send_menu(
                event,
                context,
                "Пользователи не найдены.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        await send_menu(
            event,
            context,
            "Найденные пользователи:",
            profile_admin_kb.get_users_list_kb(users),
        )

    @dp.message_callback(F.callback.payload.startswith("prof:view:"))
    async def cb_view_profile(
        event: MessageCallback,
        context: MemoryContext,
        current_user,
    ):
        """
        Показывает карточку пользователя с кнопками действий.
        """

        target_user_id = int(event.callback.payload.split(":")[-1])
        target_user = await user_repo.get_by_id(target_user_id)

        await delete_callback_message(event)

        if target_user is None:
            await send_menu(
                event,
                context,
                "Пользователь не найден.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        if target_user.role == ROLE_ROOT and not is_root(current_user):
            await send_menu(
                event,
                context,
                "Карточка root-пользователя недоступна для просмотра.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        city = None
        if target_user.city_id:
            city = await city_repo.get_by_id(target_user.city_id)

        from services.profile_service import format_user_card

        await send_menu(
            event,
            context,
            format_user_card(target_user, city.name if city else None),
            profile_admin_kb.get_user_card_actions_kb(target_user_id),
        )

    @dp.message_callback(F.callback.payload.startswith("prof:edit:"))
    async def cb_edit_profile(
        event: MessageCallback,
        context: MemoryContext,
        current_user,
    ):
        """
        Запускает форму редактирования карточки.
        Первый шаг формы формирует отдельная функция start_edit_form.
        """

        target_user_id = int(event.callback.payload.split(":")[-1])
        target_user = await user_repo.get_by_id(target_user_id)

        await delete_callback_message(event)

        if target_user is None:
            await send_menu(
                event,
                context,
                "Пользователь не найден.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        if target_user.role == ROLE_ROOT and not is_root(current_user):
            await send_menu(
                event,
                context,
                "Root-пользователя нельзя редактировать.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        await start_edit_form(event, context, target_user)
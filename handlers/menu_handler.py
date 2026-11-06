import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from keyboards import menu_kb
from utils.permissions import is_admin, is_root
from utils.ui_messages import delete_callback_message, send_menu
from handlers.user.profile_handler import show_profile_card

logger = logging.getLogger(__name__)

# === ИНСТРУКЦИИ ДЛЯ КАЖДОЙ РОЛИ ===

INSTRUCTION_TRAINER = """
📖 ИНСТРУКЦИЯ К БОТУ

👤 Мой профиль — просмотр и редактирование личных данных (должность, город, дата рождения).
📅 Мои тренинги — список назначенных тренингов и календарь команды.
📊 Статистика — статистика по тренингам и графики.
📚 Материалы тренера — ссылка на материалы для тренеров.
"""

INSTRUCTION_ADMIN = """
📖 ИНСТРУКЦИЯ К БОТУ

👤 Мой профиль — просмотр и редактирование личных данных.
📅 Мои тренинги — список назначенных тренингов.
📊 Статистика — статистика по тренингам и графики.
📚 Материалы тренера — ссылка на материалы для тренеров.

🛠️ АДМИНИСТРИРОВАНИЕ
👥 Профили пользователей — заполнение и редактирование карточек.
🎓 Тренинги — создание и управление тренингами.
🌍 Справочники — управление макрорегионами и городами.
🔑 Роли пользователей — назначение ролей.
📣 Массовая рассылка — отправка сообщений группам пользователей.
"""

INSTRUCTION_ROOT = """
📖 ИНСТРУКЦИЯ К БОТУ

👤 Мой профиль — просмотр и редактирование личных данных.
📅 Мои тренинги — список назначенных тренингов.
📊 Статистика — статистика по тренингам и графики.
📚 Материалы тренера — ссылка на материалы для тренеров.

🛠️ АДМИНИСТРИРОВАНИЕ
👥 Профили пользователей — заполнение и редактирование карточек.
🎓 Тренинги — создание и управление тренингами.
🌍 Справочники — управление макрорегионами и городами.
🔑 Роли пользователей — назначение ролей.
📣 Массовая рассылка — отправка сообщений группам пользователей.

🔧 СЛУЖЕБНЫЕ КОМАНДЫ
💾 Ручной бэкап БД — создание резервной копии базы данных.
💬 Смена ID общего чата — изменение идентификатора чата.
🔍 Диагностика системы — сводка по системе.
"""


def register_menu_handlers(
    dp: Dispatcher,
    settings,
    user_repo,
    city_repo,
    macro_repo,
    training_repo,
    report_repo,
    bot,
) -> None:
    """
    Главное меню бота.
    """

    @dp.message_created(Command("menu"))
    async def cmd_menu(event: MessageCreated, context: MemoryContext, current_user):
        await context.clear()
        await _show_menu(event, context, current_user)

    @dp.message_callback(F.callback.payload == "menu:back")
    async def cb_menu_back(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await _show_menu(event, context, current_user)

    @dp.message_callback(F.callback.payload == "menu:admin_menu")
    async def cb_admin_menu(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await send_menu(
            event, context,
            "🛠️ Администрирование:",
            menu_kb.get_admin_submenu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:root_menu")
    async def cb_root_menu(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await send_menu(
            event, context,
            "🔧 Служебные команды:",
            menu_kb.get_root_submenu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:materials")
    async def cb_materials(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        url = settings.trainer_materials_url
        if not url:
            url = "Ссылка на материалы тренера пока не настроена."
        else:
            url = f"📚 Материалы тренера:\n{url}"

        await send_menu(event, context, url, None)

    @dp.message_callback(F.callback.payload == "menu:instruction")
    async def cb_instruction(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)

        if is_root(current_user):
            text = INSTRUCTION_ROOT
        elif is_admin(current_user):
            text = INSTRUCTION_ADMIN
        else:
            text = INSTRUCTION_TRAINER

        await send_menu(event, context, text.strip(), None)

    @dp.message_callback(F.callback.payload == "menu:profile")
    async def cb_open_profile(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        await show_profile_card(
            event, context, user_repo, city_repo, current_user.user_id,
        )

    @dp.message_callback(F.callback.payload == "menu:my_trainings")
    async def cb_open_my_trainings(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        # TODO: вызвать функцию показа экрана «Мои тренинги»
        await send_menu(event, context, "Экран «Мои тренинги» будет привязан на следующем шаге.", None)

    @dp.message_callback(F.callback.payload == "menu:stats")
    async def cb_open_stats(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        # TODO: вызвать функцию показа экрана «Статистика»
        await send_menu(event, context, "Экран «Статистика» будет привязан на следующем шаге.", None)

    @dp.message_callback(F.callback.payload.startswith("menu:"))
    async def cb_menu_item_fallback(event: MessageCallback, context: MemoryContext, current_user):
        payload = event.callback.payload
        action = payload.split(":")[1]
        await delete_callback_message(event)

        commands_map = {
            "admin_profiles": "/admin_profiles",
            "admin_trainings": "/admin_trainings",
            "admin_spravochnik": "/admin_spravochnik",
            "admin_roles": "/admin_roles",
            "admin_broadcast": "/admin_broadcast",
            "root_backup": "/root_backup",
            "root_chat": "/root_chat",
            "root_diagnose": "/root_diagnose",
        }

        command = commands_map.get(action)
        if command:
            await send_menu(
                event, context,
                f"Используйте команду: {command}",
                None,
            )


async def _show_menu(event, context: MemoryContext, current_user):
    """Показывает меню в зависимости от роли пользователя."""
    if is_root(current_user):
        kb = menu_kb.get_root_menu_kb()
    elif is_admin(current_user):
        kb = menu_kb.get_admin_menu_kb()
    else:
        kb = menu_kb.get_user_menu_kb()

    await send_menu(
        event, context,
        "🏠 Главное меню:",
        kb,
    )
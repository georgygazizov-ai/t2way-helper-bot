import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from keyboards import menu_kb
from keyboards.user import profile_kb, trainings_kb as user_trainings_kb
from keyboards.common import stats_kb
from keyboards.admin import (
    profile_admin_kb,
    trainings_kb as admin_trainings_kb,
    cities_kb,
    roles_kb,
)
from handlers.user.profile_handler import show_profile_card
from utils.permissions import is_admin, is_root
from utils.ui_messages import delete_callback_message, send_menu

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
    settings_repo,
) -> None:
    """
    Главное меню бота — привязка кнопок к реальным экранам.
    """

    @dp.message_created(Command("menu"))
    async def cmd_menu(event: MessageCreated, context: MemoryContext, current_user):
        await context.clear()
        await _show_menu(event, context, current_user)

    @dp.message_callback(F.callback.payload == "menu:back")
    async def cb_menu_back(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        await _show_menu(event, context, current_user)

    # === ПОДМЕНЮ ===

    @dp.message_callback(F.callback.payload == "menu:admin_menu")
    async def cb_admin_menu(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "🛠️ Администрирование:",
            menu_kb.get_admin_submenu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:root_menu")
    async def cb_root_menu(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "🔧 Служебные команды:",
            menu_kb.get_root_submenu_kb(),
        )

    # === ВНЕШНИЕ РЕСУРСЫ И ИНСТРУКЦИИ ===

    @dp.message_callback(F.callback.payload == "menu:materials")
    async def cb_materials(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()

        url = settings.trainer_materials_url
        if not url:
            url = "Ссылка на материалы тренера пока не настроена."
        else:
            url = f"📚 Материалы тренера:\n{url}"

        await send_menu(event, context, url, None)

    @dp.message_callback(F.callback.payload == "menu:instruction")
    async def cb_instruction(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()

        if is_root(current_user):
            text = INSTRUCTION_ROOT
        elif is_admin(current_user):
            text = INSTRUCTION_ADMIN
        else:
            text = INSTRUCTION_TRAINER

        await send_menu(event, context, text.strip(), None)

    # === ПРИВЯЗКА К РЕАЛЬНЫМ ЭКРАНАМ ===

    @dp.message_callback(F.callback.payload == "menu:profile")
    async def cb_open_profile(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        await show_profile_card(
            event, context, user_repo, city_repo, current_user.user_id,
        )

    @dp.message_callback(F.callback.payload == "menu:my_trainings")
    async def cb_open_my_trainings(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Тренинги:",
            user_trainings_kb.get_my_trainings_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:stats")
    async def cb_open_stats(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Статистика по тренингам:",
            stats_kb.get_stats_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:admin_profiles")
    async def cb_open_admin_profiles(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Управление профилями пользователей:",
            profile_admin_kb.get_profile_admin_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:admin_trainings")
    async def cb_open_admin_trainings(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Управление тренингами:",
            admin_trainings_kb.get_trainings_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:admin_spravochnik")
    async def cb_open_spravochnik(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Меню управления справочниками:",
            cities_kb.get_spravochnik_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:admin_roles")
    async def cb_open_roles(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Управление ролями пользователей:",
            roles_kb.get_roles_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:admin_broadcast")
    async def cb_open_broadcast(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.clear()
        await send_menu(
            event, context,
            "Массовая рассылка.\n\nВыберите сегмент получателей:",
            menu_kb.get_segment_choice_kb(),
        )

    @dp.message_callback(F.callback.payload == "menu:root_backup")
    async def cb_open_root_backup(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        from handlers.root_handler import run_root_backup
        await run_root_backup(event, context, current_user, bot, settings)

    @dp.message_callback(F.callback.payload == "menu:root_chat")
    async def cb_open_root_chat(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        from handlers.root_handler import run_root_chat_start
        await run_root_chat_start(event, context, current_user, settings_repo)

    @dp.message_callback(F.callback.payload == "menu:root_diagnose")
    async def cb_open_root_diagnose(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        await context.clear()
        from handlers.root_handler import run_root_diagnose
        await run_root_diagnose(event, context, current_user, user_repo, training_repo, settings_repo, settings)


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
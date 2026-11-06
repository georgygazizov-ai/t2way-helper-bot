from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

def get_user_menu_kb():
    """Главное меню для обычного пользователя (тренера)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="👤 Мой профиль", payload="menu:profile"),
        CallbackButton(text="📅 Мои тренинги", payload="menu:my_trainings"),
    )
    builder.row(
        CallbackButton(text="📊 Статистика", payload="menu:stats"),
        CallbackButton(text="📚 Материалы тренера", payload="menu:materials"),
    )
    builder.row(
        CallbackButton(text="📖 Инструкция к боту", payload="menu:instruction"),
    )
    return builder.as_markup()

def get_admin_menu_kb():
    """Главное меню для администратора."""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="👤 Мой профиль", payload="menu:profile"),
        CallbackButton(text="📅 Мои тренинги", payload="menu:my_trainings"),
    )
    builder.row(
        CallbackButton(text="📊 Статистика", payload="menu:stats"),
        CallbackButton(text="📚 Материалы тренера", payload="menu:materials"),
    )
    builder.row(
        CallbackButton(text="📖 Инструкция к боту", payload="menu:instruction"),
    )
    builder.row(
        CallbackButton(text="🛠️ Администрирование", payload="menu:admin_menu"),
    )
    return builder.as_markup()

def get_root_menu_kb():
    """Главное меню для root-пользователя."""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="👤 Мой профиль", payload="menu:profile"),
        CallbackButton(text="📅 Мои тренинги", payload="menu:my_trainings"),
    )
    builder.row(
        CallbackButton(text="📊 Статистика", payload="menu:stats"),
        CallbackButton(text="📚 Материалы тренера", payload="menu:materials"),
    )
    builder.row(
        CallbackButton(text="📖 Инструкция к боту", payload="menu:instruction"),
    )
    builder.row(
        CallbackButton(text="🛠️ Администрирование", payload="menu:admin_menu"),
    )
    builder.row(
        CallbackButton(text="🔧 Служебные команды", payload="menu:root_menu"),
    )
    return builder.as_markup()

def get_admin_submenu_kb():
    """Подменю «Администрирование»."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="👥 Профили пользователей", payload="menu:admin_profiles"))
    builder.row(CallbackButton(text="🎓 Тренинги", payload="menu:admin_trainings"))
    builder.row(CallbackButton(text="🌍 Справочники", payload="menu:admin_spravochnik"))
    builder.row(CallbackButton(text="🔑 Роли пользователей", payload="menu:admin_roles"))
    builder.row(CallbackButton(text="📣 Массовая рассылка", payload="menu:admin_broadcast"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))
    return builder.as_markup()

def get_root_submenu_kb():
    """Подменю «Служебные команды»."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="💾 Ручной бэкап БД", payload="menu:root_backup"))
    builder.row(CallbackButton(text="💬 Смена ID общего чата", payload="menu:root_chat"))
    builder.row(CallbackButton(text="🔍 Диагностика системы", payload="menu:root_diagnose"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))
    return builder.as_markup()

def get_segment_choice_kb():
    """Дублирует клавиатуру из broadcast_kb для прямого вызова из меню."""
    from keyboards.admin import broadcast_kb
    return broadcast_kb.get_segment_choice_kb()

def get_back_to_main_kb():
    """Клавиатура с единственной кнопкой 'Главное меню'."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))
    return builder.as_markup()

def get_root_actions_kb():
    """Клавиатура после выполнения root-команд: возврат в root-меню и главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="🔧 В root-меню", payload="menu:root_menu"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))
    return builder.as_markup()
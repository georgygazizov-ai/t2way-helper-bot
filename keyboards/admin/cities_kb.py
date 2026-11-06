from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton


def get_spravochnik_menu_kb():
    """Главное меню справочников."""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Управление макрорегионами", payload="spr:macro_menu"),
    )
    builder.row(
        CallbackButton(text="Управление городами", payload="spr:city_menu"),
    )
    builder.row(
        CallbackButton(text="🏠 Главное меню", payload="menu:main"),
    )
    return builder.as_markup()


def get_macro_actions_kb():
    """Меню действий для макрорегионов."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Добавить макрорегион", payload="spr:macro_add"))
    builder.row(CallbackButton(text="Деактивировать макрорегион", payload="spr:macro_deactivate_list"))
    builder.row(CallbackButton(text="« Назад", payload="spr:main_menu"))
    return builder.as_markup()


def get_city_actions_kb():
    """Меню действий для городов."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Добавить город", payload="spr:city_add_start"))
    builder.row(CallbackButton(text="Деактивировать город", payload="spr:city_deactivate_list"))
    builder.row(CallbackButton(text="« Назад", payload="spr:main_menu"))
    return builder.as_markup()


def get_back_kb(payload="spr:main_menu"):
    """Универсальная кнопка 'Назад' для состояний ожидания ввода."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="« Отмена", payload=payload))
    return builder.as_markup()


def get_macro_deactivate_list_kb(regions):
    """Список макрорегионов для деактивации."""
    builder = InlineKeyboardBuilder()
    for r in regions:
        builder.row(CallbackButton(text=r.name, payload=f"spr:macro_deactivate:{r.id}"))
    builder.row(CallbackButton(text="« Назад", payload="spr:macro_menu"))
    return builder.as_markup()


def get_city_deactivate_list_kb(cities):
    """Список городов для деактивации."""
    builder = InlineKeyboardBuilder()
    for c in cities:
        builder.row(CallbackButton(text=c.name, payload=f"spr:city_deactivate:{c.id}"))
    builder.row(CallbackButton(text="« Назад", payload="spr:city_menu"))
    return builder.as_markup()


def get_macro_region_choice_kb(regions):
    """Список макрорегионов для выбора при добавлении города."""
    builder = InlineKeyboardBuilder()
    for r in regions:
        builder.row(CallbackButton(text=r.name, payload=f"spr:city_choose_macro:{r.id}"))
    builder.row(CallbackButton(text="« Отмена", payload="spr:city_menu"))
    return builder.as_markup()
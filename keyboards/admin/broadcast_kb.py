from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

def get_segment_choice_kb():
    """Главное меню выбора сегмента для рассылки."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Все пользователи", payload="brd:segment:all"))
    builder.row(CallbackButton(text="Тренеры", payload="brd:segment:trainers"))
    builder.row(CallbackButton(text="Администраторы", payload="brd:segment:admins"))
    builder.row(CallbackButton(text="По макрорегиону", payload="brd:segment:macro"))
    builder.row(CallbackButton(text="По городу", payload="brd:segment:city"))
    builder.row(CallbackButton(text="« Отмена", payload="brd:cancel"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))
    return builder.as_markup()

def get_macro_region_choice_kb(regions):
    """Выбор макрорегиона."""
    builder = InlineKeyboardBuilder()
    for region in regions:
        builder.row(CallbackButton(text=region.name, payload=f"brd:macro:{region.id}"))
    builder.row(CallbackButton(text="« Назад", payload="brd:back_to_segment"))
    return builder.as_markup()

def get_city_choice_kb(cities):
    """Выбор города."""
    builder = InlineKeyboardBuilder()
    for city in cities:
        builder.row(CallbackButton(text=city.name, payload=f"brd:city:{city.id}"))
    builder.row(CallbackButton(text="« Назад", payload="brd:back_to_segment"))
    return builder.as_markup()

def get_broadcast_preview_kb():
    """Кнопки подтверждения рассылки."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="✅ Отправить", payload="brd:confirm_send"))
    builder.row(CallbackButton(text="« Отменить рассылку", payload="brd:cancel"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))
    return builder.as_markup()

def get_broadcast_preview_kb():
    """Кнопки подтверждения рассылки."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="✅ Отправить", payload="brd:confirm_send"))
    builder.row(CallbackButton(text="« Отменить рассылку", payload="brd:cancel"))
    return builder.as_markup()

def get_skip_media_kb():
    """Кнопка перехода к предпросмотру без прикрепления файла."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Без файла (далее)", payload="brd:skip_media"))
    builder.row(CallbackButton(text="« Отменить рассылку", payload="brd:cancel"))
    return builder.as_markup()
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton


def get_user_profile_menu_kb():
    """Главное меню профиля пользователя."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Изменить должность", payload="up:edit_position"),
        CallbackButton(text="Изменить город", payload="up:edit_city"),
    )
    builder.row(
        CallbackButton(text="Изменить дату рождения", payload="up:edit_birth"),
    )
    builder.row(
        CallbackButton(text="Закрыть профиль", payload="up:close"),
    )

    return builder.as_markup()


def get_macro_region_choice_kb(regions):
    """Выбор макрорегиона при смене города."""

    builder = InlineKeyboardBuilder()

    for region in regions:
        builder.row(
            CallbackButton(
                text=region.name,
                payload=f"up:macro:{region.id}",
            )
        )

    builder.row(
        CallbackButton(text="« Отмена", payload="up:menu"),
    )

    return builder.as_markup()


def get_city_choice_kb(cities):
    """Выбор города при смене города."""

    builder = InlineKeyboardBuilder()

    for city in cities:
        builder.row(
            CallbackButton(
                text=city.name,
                payload=f"up:city:{city.id}",
            )
        )

    builder.row(
        CallbackButton(text="« Назад", payload="up:macro_back"),
    )

    return builder.as_markup()


def get_cancel_kb():
    """Кнопка отмены редактирования."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="« Отмена", payload="up:menu"),
    )

    return builder.as_markup()
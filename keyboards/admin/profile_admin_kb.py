from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from database.models import User
from services.profile_service import get_full_name


def get_profile_admin_menu_kb():
    """Главное меню управления профилями."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Незаполненные карточки", payload="prof:incomplete")
    )
    builder.row(
        CallbackButton(text="Найти по фамилии", payload="prof:search")
    )
    builder.row(
        CallbackButton(text="🏠 Главное меню", payload="menu:main")
    )

    return builder.as_markup()


def get_users_list_kb(users: list[User]):
    """Список пользователей кнопками. Кнопка открывает просмотр карточки."""

    builder = InlineKeyboardBuilder()

    for user in users:
        builder.row(
            CallbackButton(
                text=f"{get_full_name(user)} / ID {user.user_id}",
                payload=f"prof:view:{user.user_id}",
            )
        )

    builder.row(
        CallbackButton(text="« Назад", payload="prof:menu")
    )

    return builder.as_markup()


def get_user_card_actions_kb(user_id: int):
    """Кнопки действий при просмотре карточки пользователя."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Редактировать карточку", payload=f"prof:edit:{user_id}")
    )
    builder.row(
        CallbackButton(text="« Назад", payload="prof:menu")
    )

    return builder.as_markup()


def get_profile_form_step_kb():
    """Клавиатура шага формы: оставить текущее значение или отменить."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Оставить как есть", payload="prof:keep")
    )
    builder.row(
        CallbackButton(text="« Отмена", payload="prof:menu")
    )

    return builder.as_markup()


def get_macro_region_choice_kb(regions):
    """Выбор макрорегиона при заполнении профиля."""

    builder = InlineKeyboardBuilder()

    for region in regions:
        builder.row(
            CallbackButton(text=region.name, payload=f"prof:macro:{region.id}")
        )

    builder.row(
        CallbackButton(text="Оставить как есть", payload="prof:keep")
    )
    builder.row(
        CallbackButton(text="« Отмена", payload="prof:menu")
    )

    return builder.as_markup()


def get_city_choice_kb(cities):
    """Выбор города при заполнении профиля."""

    builder = InlineKeyboardBuilder()

    for city in cities:
        builder.row(
            CallbackButton(text=city.name, payload=f"prof:city:{city.id}")
        )

    builder.row(
        CallbackButton(text="Оставить как есть", payload="prof:keep")
    )
    builder.row(
        CallbackButton(text="« Назад", payload="prof:macro_back")
    )

    return builder.as_markup()


def get_cancel_profile_form_kb():
    """Кнопка отмены (используется в поиске по фамилии)."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="« Отмена", payload="prof:menu")
    )

    return builder.as_markup()
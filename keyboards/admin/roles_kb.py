from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from database.models import User
from services.profile_service import get_full_name
from utils.permissions import ROLE_ADMIN, ROLE_TRAINER


def get_roles_menu_kb():
    """Главное меню управления ролями."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Найти пользователя по фамилии", payload="roles:search")
    )
    builder.row(
        CallbackButton(text="🏠 Главное меню", payload="menu:main")
    )

    return builder.as_markup()


def get_users_list_kb(users: list[User]):
    """Список найденных пользователей для смены роли."""

    builder = InlineKeyboardBuilder()

    for user in users:
        builder.row(
            CallbackButton(
                text=f"{get_full_name(user)} / ID {user.user_id}",
                payload=f"roles:user:{user.user_id}",
            )
        )

    builder.row(
        CallbackButton(text="« Назад", payload="roles:menu")
    )

    return builder.as_markup()


def get_role_actions_kb(user: User):
    """Кнопки действий с ролью конкретного пользователя."""

    builder = InlineKeyboardBuilder()

    if user.role == ROLE_TRAINER:
        builder.row(
            CallbackButton(
                text="Назначить администратором",
                payload=f"roles:make_admin:{user.user_id}",
            )
        )

    if user.role == ROLE_ADMIN:
        builder.row(
            CallbackButton(
                text="Понизить до тренера",
                payload=f"roles:make_trainer:{user.user_id}",
            )
        )

    builder.row(
        CallbackButton(text="« Назад", payload="roles:menu")
    )

    return builder.as_markup()


def get_cancel_kb():
    """Кнопка отмены поиска."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="« Отмена", payload="roles:menu")
    )

    return builder.as_markup()
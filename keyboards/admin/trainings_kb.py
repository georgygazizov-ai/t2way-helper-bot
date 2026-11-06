from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from database.models import User
from services.profile_service import get_full_name


def get_trainings_menu_kb():
    """Главное меню управления тренингами."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Создать тренинг", payload="train:create")
    )
    builder.row(
        CallbackButton(text="Все тренинги", payload="train:list_all")
    )
    builder.row(
        CallbackButton(text="Назначенные тренинги", payload="train:list_assigned")
    )
    builder.row(
        CallbackButton(text="🏠 Главное меню", payload="menu:main")
    )

    return builder.as_markup()


def get_format_choice_kb():
    """Выбор формата тренинга."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="Basic", payload="train:format:Basic"))
    builder.row(CallbackButton(text="Leadership", payload="train:format:Leadership"))
    builder.row(CallbackButton(text="« Отмена", payload="train:menu"))

    return builder.as_markup()


def get_macro_region_choice_kb(regions):
    """Выбор макрорегиона."""

    builder = InlineKeyboardBuilder()

    for region in regions:
        builder.row(CallbackButton(text=region.name, payload=f"train:macro:{region.id}"))

    builder.row(CallbackButton(text="« Отмена", payload="train:menu"))

    return builder.as_markup()


def get_city_choice_kb(cities):
    """Выбор города."""

    builder = InlineKeyboardBuilder()

    for city in cities:
        builder.row(CallbackButton(text=city.name, payload=f"train:city:{city.id}"))

    builder.row(CallbackButton(text="« Назад", payload="train:macro_back"))

    return builder.as_markup()


def get_leads_choice_kb(trainers: list[User], selected_ids: list[int], cancel_payload: str = "train:menu"):
    """Выбор ведущих тренинга."""

    builder = InlineKeyboardBuilder()

    for trainer in trainers:
        marker = "✓ " if trainer.user_id in selected_ids else ""
        text = f"{marker}{get_full_name(trainer)}"

        builder.row(
            CallbackButton(
                text=text,
                payload=f"train:lead_toggle:{trainer.user_id}",
            )
        )

    builder.row(CallbackButton(text="Подтвердить выбор", payload="train:leads_confirm"))
    builder.row(CallbackButton(text="« Отмена", payload=cancel_payload))

    return builder.as_markup()


def get_trainings_list_kb(trainings, with_edit: bool = True):
    """Список тренингов."""

    builder = InlineKeyboardBuilder()

    for training in trainings:
        text = f"{training['date']} | {training['format']} | ID {training['id']}"

        if with_edit:
            builder.row(CallbackButton(text=text, payload=f"train:view:{training['id']}"))
        else:
            builder.row(CallbackButton(text=text, payload=f"train:view:{training['id']}"))

    builder.row(CallbackButton(text="« Назад", payload="train:menu"))

    return builder.as_markup()


def get_training_view_kb(training_id: int, status: str):
    """Кнопки просмотра тренинга."""

    builder = InlineKeyboardBuilder()

    if status == "assigned":
        builder.row(CallbackButton(text="Редактировать", payload=f"train:edit:{training_id}"))
        builder.row(CallbackButton(text="Отменить тренинг", payload=f"train:cancel:{training_id}"))

    builder.row(CallbackButton(text="« Назад", payload="train:menu"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))

    return builder.as_markup()


def get_training_edit_kb(training_id: int):
    """Кнопки редактирования тренинга."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="Изменить дату", payload=f"train:edit_date:{training_id}"))
    builder.row(CallbackButton(text="Изменить формат", payload=f"train:edit_format:{training_id}"))
    builder.row(CallbackButton(text="Изменить город", payload=f"train:edit_city:{training_id}"))
    builder.row(CallbackButton(text="Изменить ведущих", payload=f"train:edit_leads:{training_id}"))
    builder.row(CallbackButton(text="« Назад", payload=f"train:view:{training_id}"))

    return builder.as_markup()


def get_cancel_kb():
    """Кнопка отмены."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="« Отмена", payload="train:menu"))

    return builder.as_markup()


def get_training_cancel_kb(training_id: int):
    """Кнопки подтверждения отмены тренинга."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(
            text="Да, отменить",
            payload=f"train:cancel_confirm:{training_id}",
        )
    )
    builder.row(
        CallbackButton(text="Нет, не отменять", payload=f"train:view:{training_id}")
    )

    return builder.as_markup()


def get_cancel_reason_kb():
    """Кнопка пропуска причины отмены."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Без причины", payload="train:cancel_no_reason")
    )

    return builder.as_markup()
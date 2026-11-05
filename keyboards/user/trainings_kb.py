from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder


def get_my_trainings_menu_kb():
    """Меню просмотра тренингов пользователя."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="Мои предстоящие", payload="mytrain:my_upcoming")
    )
    builder.row(
        CallbackButton(text="Мои проведённые", payload="mytrain:my_done")
    )
    builder.row(
        CallbackButton(text="Календарь команды", payload="mytrain:team")
    )

    return builder.as_markup()


def get_trainings_list_kb(items, back_payload: str = "mytrain:menu"):
    """
    Список тренингов кнопками.
    items — список кортежей (training_id, текст кнопки).
    """

    builder = InlineKeyboardBuilder()

    for training_id, text in items:
        builder.row(
            CallbackButton(text=text, payload=f"mytrain:view:{training_id}")
        )

    builder.row(
        CallbackButton(text="« Назад", payload=back_payload)
    )

    return builder.as_markup()


def get_training_card_kb():
    """Кнопка возврата из карточки тренинга."""

    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="« Назад в меню", payload="mytrain:menu")
    )

    return builder.as_markup()
from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder


def get_stats_menu_kb():
    """Главное меню статистики."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="По амбассадорам", payload="stats:leads"))
    builder.row(CallbackButton(text="По городам", payload="stats:cities"))
    builder.row(CallbackButton(text="По макрорегионам", payload="stats:macro"))
    builder.row(CallbackButton(text="По месяцам", payload="stats:months"))
    builder.row(CallbackButton(text="По форматам", payload="stats:formats"))
    builder.row(CallbackButton(text="Годовой отчёт (CSV)", payload="stats:annual"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))

    return builder.as_markup()


def get_period_choice_kb(kind: str):
    """Выбор периода для выбранного среза."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="Последние 30 дней", payload=f"stats:period:{kind}:days_30"))
    builder.row(CallbackButton(text="Последние 90 дней", payload=f"stats:period:{kind}:days_90"))
    builder.row(CallbackButton(text="Последние 180 дней", payload=f"stats:period:{kind}:days_180"))
    builder.row(CallbackButton(text="Последние 365 дней", payload=f"stats:period:{kind}:days_365"))
    builder.row(CallbackButton(text="Всё время", payload=f"stats:period:{kind}:all"))
    builder.row(CallbackButton(text="Произвольный период", payload=f"stats:period:{kind}:custom"))
    builder.row(CallbackButton(text="« Назад", payload="stats:menu"))

    return builder.as_markup()


def get_year_choice_kb(years: list[str]):
    """Выбор года для годового отчёта."""

    builder = InlineKeyboardBuilder()

    for year in years:
        builder.row(CallbackButton(text=year, payload=f"stats:year:{year}"))

    builder.row(CallbackButton(text="« Назад", payload="stats:menu"))

    return builder.as_markup()


def get_custom_period_kb():
    """Кнопка отмены при вводе произвольного периода."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="« Отмена", payload="stats:menu"))

    return builder.as_markup()


def get_back_to_stats_menu_kb():
    """Возврат в главное меню статистики."""

    builder = InlineKeyboardBuilder()

    builder.row(CallbackButton(text="« Назад в меню статистики", payload="stats:menu"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:main"))

    return builder.as_markup()
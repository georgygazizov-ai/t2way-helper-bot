from database.models import User


def get_full_name(user: User) -> str:
    """
    Собирает ФИО пользователя.
    Если ФИО ещё не заполнено, возвращает ID.
    """

    parts = [
        user.last_name,
        user.first_name,
        user.patronymic,
    ]

    full_name = " ".join(part for part in parts if part)

    if full_name:
        return full_name

    return f"ID {user.user_id}"


def format_birth_date(user: User) -> str:
    """
    Красиво форматирует дату рождения.
    """

    if user.birth_day is None or user.birth_month is None:
        return "не указана"

    if user.birth_year is None:
        return f"{user.birth_day:02d}.{user.birth_month:02d}"

    return f"{user.birth_day:02d}.{user.birth_month:02d}.{user.birth_year}"


def format_user_card(user: User, city_name: str | None = None) -> str:
    """
    Текст карточки пользователя.
    """

    return (
        "Карточка пользователя:\n\n"
        f"ID: {user.user_id}\n"
        f"ФИО: {get_full_name(user)}\n"
        f"Должность: {user.position or 'не указана'}\n"
        f"Город: {city_name or 'не указан'}\n"
        f"Дата рождения: {format_birth_date(user)}\n"
        f"Роль: {user.role}\n"
        f"Статус: {user.status}\n"
        f"Профиль заполнен: {'да' if user.is_profile_complete else 'нет'}"
    )

def format_profile_for_user(user: User, city_name: str | None = None) -> str:
    """
    Короткая карточка профиля для самого пользователя.

    Служебные поля не показываем:
    - ID;
    - роль;
    - статус;
    - признак заполненности профиля.
    """

    return (
        "Ваш профиль:\n\n"
        f"ФИО: {get_full_name(user)}\n"
        f"Должность: {user.position or 'не указана'}\n"
        f"Город: {city_name or 'не указан'}\n"
        f"Дата рождения: {format_birth_date(user)}"
    )
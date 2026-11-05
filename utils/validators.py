from datetime import date, datetime
import re


# Разрешаем буквы, цифры, дефис и пробел.
# Пробел нужен для должностей и названий городов/филиалов.
TEXT_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё0-9\- ]+$")


def validate_text_field(value: str, field_name: str) -> str:
    """
    Проверяет текстовое поле.
    Возвращает очищенную строку.
    """

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} не может быть пустым.")

    if not TEXT_PATTERN.match(value):
        raise ValueError(
            f"{field_name} может содержать только буквы, цифры, дефис и пробелы."
        )

    # Убираем лишние повторяющиеся пробелы.
    return " ".join(value.split())


def parse_birth_date(value: str) -> tuple[int, int, int | None]:
    """
    Проверяет дату рождения.

    Допустимые форматы:
    - ДД.ММ.ГГГГ
    - ДД.ММ

    Возвращает:
    (day, month, year)
    """

    value = value.strip()
    parts = value.split(".")

    if len(parts) not in (2, 3):
        raise ValueError("Дата рождения должна быть в формате ДД.ММ.ГГГГ или ДД.ММ.")

    if not all(part.isdigit() for part in parts):
        raise ValueError("Дата рождения должна содержать только цифры и точки.")

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2]) if len(parts) == 3 else None

    # Если год не указан, проверяем дату на високосном годе,
    # чтобы разрешить 29.02.
    check_year = year if year is not None else 2000

    try:
        date(check_year, month, day)
    except ValueError:
        raise ValueError("Некорректная дата рождения.")

    if year is not None and year <= 1900:
        raise ValueError("Год рождения должен быть больше 1900.")

    return day, month, year


def parse_date_to_iso(value: str) -> str:
    """
    Проверяет дату в формате ДД.ММ.ГГГГ.
    Возвращает строку YYYY-MM-DD для БД и сравнений.
    """

    value = value.strip()
    parts = value.split(".")

    if len(parts) != 3:
        raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ.")

    if not all(part.isdigit() for part in parts):
        raise ValueError("Дата должна содержать только цифры и точки.")

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])

    try:
        date_obj = datetime(year, month, day)
    except ValueError:
        raise ValueError("Некорректная дата.")

    return date_obj.strftime("%Y-%m-%d")
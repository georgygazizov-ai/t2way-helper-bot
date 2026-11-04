from datetime import datetime


def parse_training_date(value: str) -> str:
    """
    Проверяет дату тренинга в формате ДД.ММ.ГГГГ.
    Возвращает дату в формате YYYY-MM-DD для БД.
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


def format_training_date(date_str: str) -> str:
    """
    Форматирует дату из БД (YYYY-MM-DD) в читаемый вид (ДД.ММ.ГГГГ).
    """

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return date_str

def format_lead_name(lead_row) -> str:
    """
    Собирает ФИО ведущего из сырой строки БД.
    sqlite3.Row отдаёт поля только через ["имя_поля"].
    """

    parts = [
        lead_row["last_name"],
        lead_row["first_name"],
        lead_row["patronymic"],
    ]

    full_name = " ".join(part for part in parts if part)

    return full_name or f"ID {lead_row['user_id']}"
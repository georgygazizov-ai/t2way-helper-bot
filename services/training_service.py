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

async def notify_training_cancellation(
    bot,
    training_repo,
    user_repo,
    training_id: int,
    reason: str | None,
    cancelled_by_name: str,
) -> None:
    """
    Отправляет уведомления об отмене тренинга ведущим и всем администраторам.
    """

    import logging
    logger = logging.getLogger(__name__)

    # Получаем информацию о тренинге
    training = await training_repo.get_by_id(training_id)
    if not training:
        return

    leads = await training_repo.get_leads(training_id)
    admins = await user_repo.get_admins()

    date_str = format_training_date(training["date"])
    reason_text = f"\nПричина: {reason}" if reason else ""

    # Уведомляем ведущих
    for lead in leads:
        lead_user = await user_repo.get_by_id(lead["user_id"])
        if lead_user and lead_user.chat_id:
            try:
                await bot.send_message(
                    chat_id=lead_user.chat_id,
                    text=(
                        f"Тренинг {date_str} ({training['format']}) отменён.{reason_text}\n\n"
                        f"Отменил: {cancelled_by_name}"
                    ),
                )
            except Exception as exc:
                logger.warning(
                    "[ERROR] Не удалось уведомить ведущего %s об отмене тренинга: %r",
                    lead["user_id"],
                    exc,
                )

    # Уведомляем администраторов
    for admin in admins:
        if admin.chat_id:
            try:
                await bot.send_message(
                    chat_id=admin.chat_id,
                    text=(
                        f"Тренинг ID {training_id} ({date_str}, {training['format']}) отменён.{reason_text}\n\n"
                        f"Отменил: {cancelled_by_name}"
                    ),
                )
            except Exception as exc:
                logger.warning(
                    "[ERROR] Не удалось уведомить администратора %s об отмене тренинга: %r",
                    admin.user_id,
                    exc,
                )
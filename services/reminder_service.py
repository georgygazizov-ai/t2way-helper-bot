import logging
from datetime import datetime, timedelta

from repositories.city_repo import CityRepo
from repositories.reminder_repo import ReminderRepo
from repositories.training_repo import TrainingRepo
from repositories.user_repo import UserRepo
from services.training_service import format_lead_name, format_training_date
from utils.time_utils import reminder_utc_str_for_date


logger = logging.getLogger(__name__)

REMINDER_WEEK = "week_before"
REMINDER_DAY = "day_before"


async def schedule_training_reminders(
    reminder_repo: ReminderRepo,
    training_id: int,
    training_date: str,
    lead_user_ids: list[int],
    timezone_name: str,
) -> int:
    """
    Создаёт отложенные напоминания для каждого ведущего:
    - за неделю до тренинга (09:00 МСК);
    - за день до тренинга (09:00 МСК).

    Если момент напоминания уже прошёл, оно не создаётся.
    Возвращает количество созданных напоминаний.
    """

    base_date = datetime.strptime(training_date, "%Y-%m-%d").date()

    plan = [
        (REMINDER_WEEK, (base_date - timedelta(days=7)).isoformat()),
        (REMINDER_DAY, (base_date - timedelta(days=1)).isoformat()),
    ]

    count = 0

    for reminder_type, target_date in plan:
        scheduled_for = reminder_utc_str_for_date(target_date, timezone_name)

        if scheduled_for is None:
            # Время уже прошло — напоминание не создаём.
            continue

        for user_id in lead_user_ids:
            await reminder_repo.create(
                training_id,
                user_id,
                reminder_type,
                scheduled_for,
            )
            count += 1

    return count


def _leads_line(leads, exclude_user_id: int | None = None) -> str:
    """
    Собирает строку со списком ведущих.
    Если exclude_user_id задан, этот ведущий не включается в список.
    """

    names = [
        format_lead_name(lead)
        for lead in leads
        if exclude_user_id is None or lead["user_id"] != exclude_user_id
    ]

    return ", ".join(names) if names else "вы единственный ведущий"


async def notify_leads_assignment(
    bot,
    user_repo: UserRepo,
    city_repo: CityRepo,
    training,
    leads,
) -> None:
    """
    Отправляет ведущим уведомление о назначении на тренинг.
    В уведомлении указывается список со-ведущих.
    """

    city = await city_repo.get_by_id(training["city_id"])
    city_name = city.name if city else "город не указан"

    for lead in leads:
        user = await user_repo.get_by_id(lead["user_id"])

        if user is None or user.chat_id is None:
            logger.warning(
                "[ERROR] У ведущего %s нет диалога с ботом — уведомление о назначении не отправлено",
                lead["user_id"],
            )
            continue

        others = _leads_line(leads, exclude_user_id=lead["user_id"])

        try:
            await bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "Вы назначены ведущим тренинга.\n\n"
                    f"Дата: {format_training_date(training['date'])}\n"
                    f"Формат: {training['format']}\n"
                    f"Город: {city_name}\n"
                    f"Со-ведущие: {others}"
                ),
            )
        except Exception as exc:
            logger.warning(
                "[ERROR] Не удалось уведомить ведущего %s о назначении: %r",
                lead["user_id"],
                exc,
            )


async def notify_leads_training_changed(
    bot,
    user_repo: UserRepo,
    city_repo: CityRepo,
    training_repo: TrainingRepo,
    training_id: int,
    changed_text: str,
) -> None:
    """
    Уведомляет всех ведущих об изменении тренинга
    и показывает новые данные.
    """

    training = await training_repo.get_by_id(training_id)

    if training is None:
        return

    leads = await training_repo.get_leads(training_id)

    city = await city_repo.get_by_id(training["city_id"])
    city_name = city.name if city else "город не указан"

    leads_names = _leads_line(leads)

    for lead in leads:
        user = await user_repo.get_by_id(lead["user_id"])

        if user is None or user.chat_id is None:
            logger.warning(
                "[ERROR] У ведущего %s нет диалога с ботом — уведомление об изменении не отправлено",
                lead["user_id"],
            )
            continue

        try:
            await bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "Тренинг, на котором вы ведущий, изменён.\n\n"
                    f"Что изменилось: {changed_text}\n\n"
                    f"Дата: {format_training_date(training['date'])}\n"
                    f"Формат: {training['format']}\n"
                    f"Город: {city_name}\n"
                    f"Ведущие: {leads_names}"
                ),
            )
        except Exception as exc:
            logger.warning(
                "[ERROR] Не удалось уведомить ведущего %s об изменении тренинга: %r",
                lead["user_id"],
                exc,
            )
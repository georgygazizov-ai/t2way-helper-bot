import logging

from repositories.city_repo import CityRepo
from repositories.reminder_repo import ReminderRepo
from repositories.training_repo import TrainingRepo
from repositories.user_repo import UserRepo
from services.training_service import format_lead_name, format_training_date
from utils.time_utils import now_utc_str, today_str_in_tz


logger = logging.getLogger(__name__)


async def send_due_reminders(
    bot,
    reminder_repo: ReminderRepo,
    user_repo: UserRepo,
    training_repo: TrainingRepo,
    city_repo: CityRepo,
) -> None:
    """
    Отправляет напоминания, у которых наступило время отправки.
    Запускается планировщиком каждую минуту.
    """

    now = now_utc_str()
    due = await reminder_repo.get_due(now)

    for reminder in due:
        training = await training_repo.get_by_id(reminder["training_id"])

        # Тренинг исчез или уже не активен — не отправляем.
        if training is None or training["status"] != "assigned":
            await reminder_repo.mark_sent(reminder["id"], now)
            continue

        user = await user_repo.get_by_id(reminder["user_id"])

        # Пользователь недоступен — не отправляем.
        if user is None or user.status != "active" or user.chat_id is None:
            await reminder_repo.mark_sent(reminder["id"], now)
            continue

        city = await city_repo.get_by_id(training["city_id"])
        city_name = city.name if city else "город не указан"

        if reminder["reminder_type"] == "week_before":
            when = "через 7 дней"
        elif reminder["reminder_type"] == "day_before":
            when = "завтра"
        else:
            when = "скоро"

        leads = await training_repo.get_leads(training["id"])
        co_names = [
            format_lead_name(lead)
            for lead in leads
            if lead["user_id"] != user.user_id
        ]
        co_leads = ", ".join(co_names) if co_names else "вы единственный ведущий"

        text = (
            f"Напоминание: {when} ({format_training_date(training['date'])}) "
            "вы ведёте тренинг.\n\n"
            f"Формат: {training['format']}\n"
            f"Город: {city_name}\n"
            f"Со-ведущие: {co_leads}"
        )

        try:
            await bot.send_message(chat_id=user.chat_id, text=text)
        except Exception as exc:
            logger.warning(
                "[ERROR] Не удалось отправить напоминание %s: %r",
                reminder["id"],
                exc,
            )

        await reminder_repo.mark_sent(reminder["id"], now)

        logger.info(
            "[SYSTEM] Отправлено напоминание %s (%s) пользователю %s",
            reminder["id"],
            reminder["reminder_type"],
            user.user_id,
        )


async def auto_conduct_trainings(
    training_repo: TrainingRepo,
    timezone_name: str,
) -> None:
    """
    Переводит просроченные назначенные тренинги в статус «Проведён».

    Вызывается при старте бота (исправление после простоя)
    и каждую ночь в 00:05 по Москве.
    """

    today = today_str_in_tz(timezone_name)

    trainings = await training_repo.get_assigned_before(today)

    for training in trainings:
        await training_repo.mark_conducted(training["id"])

    if trainings:
        logger.info(
            "[SYSTEM] Автоматически переведено в 'conducted': %s тренингов",
            len(trainings),
        )


def register_training_jobs(
    scheduler,
    bot,
    reminder_repo: ReminderRepo,
    user_repo: UserRepo,
    training_repo: TrainingRepo,
    city_repo: CityRepo,
    timezone_name: str,
) -> None:
    """
    Регистрирует фоновые задачи по тренингам в планировщике.
    """

    scheduler.add_job(
        func=send_due_reminders,
        trigger="interval",
        minutes=1,
        kwargs={
            "bot": bot,
            "reminder_repo": reminder_repo,
            "user_repo": user_repo,
            "training_repo": training_repo,
            "city_repo": city_repo,
        },
        id="send_due_reminders",
        name="Отправка напоминаний о тренингах",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.add_job(
        func=auto_conduct_trainings,
        trigger="cron",
        hour=0,
        minute=5,
        kwargs={
            "training_repo": training_repo,
            "timezone_name": timezone_name,
        },
        id="auto_conduct_trainings",
        name="Авто-перевод тренингов в проведённые",
        max_instances=1,
        replace_existing=True,
    )

    logger.info(
        "[SYSTEM] Задачи зарегистрированы: напоминания (каждую минуту), "
        "авто-статусы (ежедневно 00:05 МСК)"
    )
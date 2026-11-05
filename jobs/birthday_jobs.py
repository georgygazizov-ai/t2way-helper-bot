import logging

from repositories.daily_log_repo import DailyLogRepo
from repositories.user_repo import UserRepo
from services.profile_service import get_full_name
from utils.time_utils import now_utc_str, today_str_in_tz


logger = logging.getLogger(__name__)

BIRTHDAY_EVENT = "birthdays"


async def send_birthdays(
    bot,
    user_repo: UserRepo,
    daily_log_repo: DailyLogRepo,
    settings,
) -> None:
    """
    Поздравляет именинников:
    - одно общее сообщение в общий чат со списком ФИО;
    - личное поздравление каждому имениннику.

    За день отправляется только один раз.
    """

    today = today_str_in_tz(settings.timezone)

    # Сегодня уже поздравляли — не повторяем.
    if await daily_log_repo.is_done(BIRTHDAY_EVENT, today):
        return

    day = int(today[8:10])
    month = int(today[5:7])

    users = await user_repo.get_birthday_users(day, month)

    if not users:
        # Именинников нет: день помечаем проверенным,
        # чтобы при перезапусках не выполнять проверку заново.
        await daily_log_repo.mark_done(BIRTHDAY_EVENT, today, now_utc_str())
        return

    names = "\n".join(f"— {get_full_name(user)}" for user in users)

    text = (
        "🎉 Сегодня день рождения отмечают:\n"
        f"{names}\n\n"
        "Поздравляем, коллеги!"
    )

    # Сообщение в общий чат.
    try:
        await bot.send_message(chat_id=settings.common_chat_id, text=text)
    except Exception as exc:
        logger.warning(
            "[ERROR] Не удалось отправить поздравление в общий чат: %r",
            exc,
        )

    # Личное поздравление каждому имениннику.
    for user in users:
        if user.chat_id is None:
            continue

        try:
            await bot.send_message(
                chat_id=user.chat_id,
                text=(
                    "С днём рождения! 🎉\n\n"
                    "Команда T2Way желает вам успехов, "
                    "отличных тренингов и благодарных участников!"
                ),
            )
        except Exception as exc:
            logger.warning(
                "[ERROR] Не удалось лично поздравить пользователя %s: %r",
                user.user_id,
                exc,
            )

    await daily_log_repo.mark_done(BIRTHDAY_EVENT, today, now_utc_str())

    logger.info(
        "[SYSTEM] Отправлены поздравления с днём рождения: %s чел.",
        len(users),
    )


def register_birthday_jobs(
    scheduler,
    bot,
    user_repo: UserRepo,
    daily_log_repo: DailyLogRepo,
    settings,
) -> None:
    """
    Регистрирует ежедневную задачу поздравлений в 09:00 МСК.
    """

    scheduler.add_job(
        func=send_birthdays,
        trigger="cron",
        hour=9,
        minute=0,
        kwargs={
            "bot": bot,
            "user_repo": user_repo,
            "daily_log_repo": daily_log_repo,
            "settings": settings,
        },
        id="send_birthdays",
        name="Поздравления с днями рождения",
        max_instances=1,
        replace_existing=True,
    )

    logger.info("[SYSTEM] Задача дней рождения зарегистрирована (ежедневно 09:00 МСК)")
import asyncio
import logging

from maxapi import Bot, Dispatcher

from config.settings import load_settings
from database.connection import Database
from database.init_db import init_database
from handlers.system_handler import register_system_handlers
from handlers.user.start_handler import register_start_handler
from handlers.user.profile_handler import register_user_profile_handlers
from handlers.admin.cities_handler import register_spravochnik_handlers
from handlers.admin.profile_admin_handler import register_profile_admin_handlers
from handlers.admin.profile_admin_form_handler import register_profile_admin_form_handlers
from handlers.admin.roles_handler import register_roles_handlers
from handlers.admin.trainings_handler import register_trainings_handlers
from middlewares.auth_middleware import AuthMiddleware
from middlewares.role_middleware import RoleMiddleware
from repositories.user_repo import UserRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.city_repo import CityRepo
from repositories.training_repo import TrainingRepo
from services.bootstrap_service import ensure_root_users
from services.membership_service import MembershipService
from utils.logger import setup_logging
from jobs.scheduler import create_scheduler
from repositories.reminder_repo import ReminderRepo


logger = logging.getLogger(__name__)


async def main() -> None:
    settings = load_settings()

    setup_logging(
        log_dir=settings.log_dir,
        timezone_name=settings.timezone,
    )

    logger.info("[SYSTEM] Запуск T2Way Helper Bot")
    logger.info("[SYSTEM] Окружение: %s", settings.app_env)
    logger.info("[SYSTEM] Root ID: %s", settings.root_user_ids)
    logger.info("[SYSTEM] Режим проверки чата: %s", settings.membership_mode)

    db = Database(settings.db_path)
    bot = None

    try:
        await db.connect()
        await init_database(db)

        # Инициализация репозиториев
        user_repo = UserRepo(db)
        macro_repo = MacroRegionRepo(db)
        city_repo = CityRepo(db)
        training_repo = TrainingRepo(db)
        reminder_repo = ReminderRepo(db)

        # Планировщик фоновых задач: напоминания, авто-статусы, бэкапы.
        scheduler = create_scheduler(settings.timezone)
        scheduler.start()
        logger.info("[SYSTEM] Планировщик запущен")

        await ensure_root_users(user_repo, settings)

        bot = Bot(token=settings.bot_token)
        dp = Dispatcher()

        # Middleware
        dp.register_outer_middleware(AuthMiddleware(user_repo))
        dp.register_outer_middleware(RoleMiddleware())

        membership_service = MembershipService(settings)

        # Регистрация хендлеров
        register_system_handlers(dp)
        register_start_handler(dp, bot, user_repo, membership_service)
        register_spravochnik_handlers(dp, macro_repo, city_repo)
        register_profile_admin_handlers(dp, bot, user_repo, city_repo, macro_repo)
        register_profile_admin_form_handlers(dp, bot, user_repo, city_repo, macro_repo)
        register_user_profile_handlers(dp, user_repo, city_repo, macro_repo)
        register_roles_handlers(dp, bot, user_repo)
        register_trainings_handlers(dp, bot, training_repo, user_repo, city_repo, macro_repo)

        logger.info("[SYSTEM] Обработчики зарегистрированы")
        logger.info("[SYSTEM] Запуск polling")

        await dp.start_polling(bot)

    except asyncio.CancelledError:
        logger.info("[SYSTEM] Работа бота отменена")
        raise

    except Exception:
        logger.exception("[ERROR] Критическая ошибка при работе бота")
        raise

    finally:
        if bot is not None:
            try:
                if hasattr(bot, "close"):
                    await bot.close()
                elif hasattr(bot, "_session") and bot._session is not None:
                    await bot._session.close()
            except Exception:
                pass

        # Останавливаем планировщик до закрытия БД.
        if "scheduler" in locals():
            scheduler.shutdown(wait=False)
            logger.info("[SYSTEM] Планировщик остановлен")

        await db.close()
        logger.info("[SYSTEM] T2Way Helper Bot остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
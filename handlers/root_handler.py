import asyncio
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated, InputMedia

from repositories.user_repo import UserRepo
from repositories.settings_repo import SettingsRepo
from repositories.training_repo import TrainingRepo
from states.admin_states import AdminRootStates
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu
from utils.permissions import ROLE_ROOT, is_root
from utils.time_utils import now_utc_str
from config.settings import Settings

logger = logging.getLogger(__name__)

def register_root_handlers(
    dp: Dispatcher,
    bot,
    db,
    user_repo: UserRepo,
    training_repo: TrainingRepo,
    settings_repo: SettingsRepo,
    settings: Settings,
) -> None:
    """
    Служебные команды для root-пользователей.
    """

    # === РУЧНОЙ БЭКАП ===

    @dp.message_created(Command("root_backup"))
    async def cmd_root_backup(event: MessageCreated, context: MemoryContext, current_user):
        """Создаёт ручной бэкап БД в папку с бэкапами и отправляет файл в чат."""

        if not is_root(current_user):
            return

        await send_menu(
            event, context,
            "⏳ Создаю резервную копию базы данных...",
            None,
        )

        try:
            # Создаём папку для бэкапов, если её нет
            settings.backup_dir.mkdir(parents=True, exist_ok=True)

            # Формируем имя файла
            timestamp = now_utc_str().replace(":", "-").replace(" ", "_")
            db_copy_name = f"t2way_{timestamp}.sqlite3"
            db_copy_path = settings.backup_dir / db_copy_name
            
            # Копируем БД в папку с бэкапами
            await asyncio.to_thread(shutil.copy2, str(settings.db_path), str(db_copy_path))

            # Создаём ZIP-архив
            zip_name = f"t2way_backup_{timestamp}.zip"
            zip_path = settings.backup_dir / zip_name

            await asyncio.to_thread(
                shutil.make_archive,
                str(zip_path.with_suffix("")),
                "zip",
                root_dir=str(settings.backup_dir),
                base_dir=db_copy_name,
            )

            # Удаляем временный файл БД после архивации (оставляем только ZIP)
            db_copy_path.unlink(missing_ok=True)

            # Отправляем файл администратору
            uploaded = await bot.upload_media(InputMedia(path=str(zip_path)))
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=f"✅ Резервная копия создана и сохранена в {settings.backup_dir}:",
                attachments=[uploaded],
            )

            logger.info("[ROOT] Ручной бэкап создан и отправлен пользователю %s", current_user.user_id)

        except Exception as exc:
            logger.exception("[ERROR] Ошибка при создании ручного бэкапа")
            await send_menu(
                event, context,
                f"❌ Ошибка при создании бэкапа: {exc}",
                None,
            )

    # === СМЕНА ID ОБЩЕГО ЧАТА ===

    @dp.message_created(Command("root_chat"))
    async def cmd_root_chat(event: MessageCreated, context: MemoryContext, current_user):
        """Запускает смену ID общего чата."""

        if not is_root(current_user):
            return

        await context.clear()
        await context.set_state(AdminRootStates.waiting_chat_id)

        await send_menu(
            event, context,
            "Введите новый ID общего чата (число):\n"
            "Для отмены отправьте /cancel",
            None,
        )

    @dp.message_created(AdminRootStates.waiting_chat_id, F.message.body.text)
    async def fsm_root_chat_id(event: MessageCreated, context: MemoryContext, current_user):
        await clear_last_bot_message(context)

        text = event.message.body.text.strip()

        if text.lower() == "/cancel":
            await context.clear()
            await send_menu(event, context, "Смена ID чата отменена.", None)
            return

        try:
            chat_id = int(text)
        except ValueError:
            await send_menu(
                event, context,
                "❌ Неверный формат. Введите числовое значение ID чата:",
                None,
            )
            return

        await settings_repo.set("common_chat_id", str(chat_id))
        await context.clear()

        logger.info("[ROOT] ID общего чата обновлён на %s пользователем %s", chat_id, current_user.user_id)

        await send_menu(
            event, context,
            f"✅ ID общего чата обновлён на {chat_id}.\n"
            "Изменение вступит в силу для новых проверок.",
            None,
        )

    # === ДИАГНОСТИКА ===

    @dp.message_created(Command("root_diagnose"))
    async def cmd_root_diagnose(event: MessageCreated, context: MemoryContext, current_user):
        """Выводит диагностическую информацию о системе."""

        if not is_root(current_user):
            return

        # Собираем статистику из БД
        users_count = await user_repo.count_active()
        trainings_count = await training_repo.count_all()

        # Размер файла БД
        db_size = settings.db_path.stat().st_size if settings.db_path.exists() else 0
        db_size_mb = db_size / (1024 * 1024)

        # Получаем сохранённый чат
        saved_chat_id = await settings_repo.get("common_chat_id", "не задан")

        text = (
            f"🔧 ДИАГНОСТИКА СИСТЕМЫ\n\n"
            f"Окружение: {settings.app_env}\n"
            f"Часовой пояс: {settings.timezone}\n"
            f"Режим проверки чата: {settings.membership_mode}\n\n"
            f"📊 База данных:\n"
            f"— Активных пользователей: {users_count}\n"
            f"— Всего тренингов: {trainings_count}\n"
            f"— Размер БД: {db_size_mb:.2f} МБ\n"
            f"— Путь: {settings.db_path}\n\n"
            f"💬 ID общего чата (БД): {saved_chat_id}\n"
            f"💬 ID общего чата (.env): {settings.common_chat_id or 'не задан'}\n\n"
            f"⚙️ Рассылка:\n"
            f"— Задержка: {settings.broadcast_delay_seconds} сек"
        )

        await send_menu(event, context, text, None)
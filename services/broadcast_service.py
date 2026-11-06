import asyncio
import logging
from pathlib import Path

from maxapi import Bot
from maxapi.types import InputMedia

from config.settings import Settings

logger = logging.getLogger(__name__)

async def send_broadcast_task(
    bot: Bot,
    admin_chat_id: int,
    chat_ids: list[int],
    text: str,
    media_path: str | None,
    settings: Settings,
) -> None:
    """
    Фоновая задача массовой рассылки.
    Отправляет сообщения с задержкой и присылает отчёт администратору.
    """
    total = len(chat_ids)
    success_count = 0
    error_count = 0
    
    attachments = None
    
    # 1. Загружаем медиа один раз перед началом рассылки
    if media_path:
        try:
            path = Path(media_path)
            if path.exists():
                uploaded = await bot.upload_media(InputMedia(path=str(path)))
                attachments = [uploaded]
                logger.info("[BROADCAST] Медиа успешно загружено: %s", media_path)
            else:
                logger.warning("[BROADCAST] Файл медиа не найден: %s", media_path)
        except Exception as exc:
            logger.error("[BROADCAST] Ошибка загрузки медиа: %r", exc)
            
    logger.info("[BROADCAST] Начало рассылки для %s пользователей", total)
    
    # 2. Итерируемся по получателям с задержкой
    for i, chat_id in enumerate(chat_ids, 1):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                attachments=attachments,
            )
            success_count += 1
        except Exception as exc:
            error_count += 1
            logger.warning("[BROADCAST] Ошибка отправки пользователю %s: %r", chat_id, exc)
            
        # Делаем паузу между сообщениями, кроме последнего
        if i < total:
            await asyncio.sleep(settings.broadcast_delay_seconds)
            
    # 3. Формируем и отправляем отчёт
    report = (
        f"📊 ОТЧЁТ О РАССЫЛКЕ\n\n"
        f"Всего получателей: {total}\n"
        f"Успешно: {success_count}\n"
        f"Ошибок: {error_count}"
    )
    
    try:
        await bot.send_message(chat_id=admin_chat_id, text=report)
    except Exception as exc:
        logger.error("[BROADCAST] Не удалось отправить отчёт администратору: %r", exc)
        
    # 4. Удаляем временный файл после завершения рассылки
    if media_path:
        try:
            Path(media_path).unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("[BROADCAST] Не удалось удалить временный файл %s: %r", media_path, exc)
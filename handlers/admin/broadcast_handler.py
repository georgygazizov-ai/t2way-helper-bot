import asyncio
import logging
import urllib.request
import time
from pathlib import Path

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from keyboards.admin import broadcast_kb
from repositories.city_repo import CityRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.user_repo import UserRepo
from states.admin_states import AdminBroadcastStates
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu
from utils.event_helpers import get_event_chat_id
from config.settings import Settings
from services.broadcast_service import send_broadcast_task

logger = logging.getLogger(__name__)

async def download_media(url: str, save_path: Path) -> bool:
    """Скачивает файл синхронно в отдельном потоке, чтобы не блокировать loop."""
    try:
        await asyncio.to_thread(urllib.request.urlretrieve, url, str(save_path))
        return True
    except Exception as exc:
        logger.warning("[ERROR] Не удалось скачать файл %s: %r", url, exc)
        return False

async def _show_broadcast_preview(event, context: MemoryContext, media_path: Path | None):
    """Показывает предпросмотр рассылки и ожидает подтверждения."""
    data = await context.get_data()
    segment_name = data.get("broadcast_segment_name", "неизвестный")
    text = data.get("broadcast_text", "")
    count = len(data.get("broadcast_chat_ids", []))
    
    if media_path:
        await context.update_data(broadcast_media_path=str(media_path))
        media_note = f"Файл: прикреплён ({media_path.name})\n"
    else:
        await context.update_data(broadcast_media_path=None)
        media_note = "Файл: нет\n"
        
    preview_text = (
        f"📣 ПРЕДПРОСМОТР РАССЫЛКИ\n\n"
        f"Сегмент: {segment_name}\n"
        f"Получателей: {count}\n"
        f"{media_note}\n"
        f"--- Текст сообщения ---\n{text}\n"
        f"-----------------------\n\n"
        f"Нажмите «Отправить» для запуска рассылки."
    )
    
    await context.set_state(AdminBroadcastStates.waiting_confirm)
    await send_menu(
        event,
        context,
        preview_text,
        broadcast_kb.get_broadcast_preview_kb(),
    )

def register_broadcast_handlers(
    dp: Dispatcher,
    bot,
    user_repo: UserRepo,
    city_repo: CityRepo,
    macro_repo: MacroRegionRepo,
    settings: Settings,
) -> None:
    """
    Этап 9: Массовые рассылки (выбор сегмента, текст, медиа, предпросмотр).
    """

    @dp.message_created(Command("admin_broadcast"))
    async def cmd_broadcast_start(event: MessageCreated, context: MemoryContext):
        await context.clear()
        await send_menu(
            event, context,
            "Массовая рассылка.\n\nВыберите сегмент получателей:",
            broadcast_kb.get_segment_choice_kb(),
        )

    @dp.message_callback(F.callback.payload == "brd:cancel")
    async def cb_broadcast_cancel(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)
        await send_menu(event, context, "Рассылка отменена.", None)

    @dp.message_callback(F.callback.payload == "brd:back_to_segment")
    async def cb_broadcast_back(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await send_menu(event, context, "Выберите сегмент получателей:", broadcast_kb.get_segment_choice_kb())

    @dp.message_callback(F.callback.payload.startswith("brd:segment:"))
    async def cb_segment_choice(event: MessageCallback, context: MemoryContext):
        segment = event.callback.payload.split(":")[-1]
        await delete_callback_message(event)
        users, segment_name = [], ""
        
        if segment == "all":
            users, segment_name = await user_repo.get_all_for_broadcast(), "Все пользователи"
        elif segment == "trainers":
            users, segment_name = await user_repo.get_trainers_for_broadcast(), "Тренеры"
        elif segment == "admins":
            users, segment_name = await user_repo.get_admins_for_broadcast(), "Администраторы"
        elif segment == "macro":
            macro_regions = await macro_repo.get_all_active()
            if not macro_regions:
                await send_menu(event, context, "Нет активных макрорегионов.", broadcast_kb.get_segment_choice_kb())
                return
            await send_menu(event, context, "Выберите макрорегион:", broadcast_kb.get_macro_region_choice_kb(macro_regions))
            return
        elif segment == "city":
            cities = await city_repo.get_all_active()
            if not cities:
                await send_menu(event, context, "Нет активных городов.", broadcast_kb.get_segment_choice_kb())
                return
            await send_menu(event, context, "Выберите город:", broadcast_kb.get_city_choice_kb(cities))
            return

        if not users:
            await send_menu(event, context, f"В сегменте «{segment_name}» нет пользователей с доступным chat_id.", broadcast_kb.get_segment_choice_kb())
            return

        await context.update_data(
            broadcast_segment=segment, broadcast_segment_name=segment_name,
            broadcast_user_ids=[u.user_id for u in users], broadcast_chat_ids=[u.chat_id for u in users],
        )
        await context.set_state(AdminBroadcastStates.waiting_text)
        await send_menu(event, context, f"Сегмент: {segment_name} ({len(users)} чел.).\n\nВведите текст сообщения:", broadcast_kb.get_cancel_broadcast_kb())

    @dp.message_callback(F.callback.payload.startswith("brd:macro:"))
    async def cb_macro_choice(event: MessageCallback, context: MemoryContext):
        macro_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)
        users = await user_repo.get_by_macro_region_for_broadcast(macro_id)
        macro = await macro_repo.get_by_id(macro_id)
        segment_name = f"Макрорегион: {macro.name if macro else 'неизвестный'}"
        if not users:
            await send_menu(event, context, "В макрорегионе нет пользователей.", broadcast_kb.get_segment_choice_kb())
            return
        await context.update_data(
            broadcast_segment="macro", broadcast_segment_name=segment_name,
            broadcast_user_ids=[u.user_id for u in users], broadcast_chat_ids=[u.chat_id for u in users],
        )
        await context.set_state(AdminBroadcastStates.waiting_text)
        await send_menu(event, context, f"Сегмент: {segment_name} ({len(users)} чел.).\n\nВведите текст сообщения:", broadcast_kb.get_cancel_broadcast_kb())

    @dp.message_callback(F.callback.payload.startswith("brd:city:"))
    async def cb_city_choice(event: MessageCallback, context: MemoryContext):
        city_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)
        users = await user_repo.get_by_city_for_broadcast(city_id)
        city = await city_repo.get_by_id(city_id)
        segment_name = f"Город: {city.name if city else 'неизвестный'}"
        if not users:
            await send_menu(event, context, "В городе нет пользователей.", broadcast_kb.get_segment_choice_kb())
            return
        await context.update_data(
            broadcast_segment="city", broadcast_segment_name=segment_name,
            broadcast_user_ids=[u.user_id for u in users], broadcast_chat_ids=[u.chat_id for u in users],
        )
        await context.set_state(AdminBroadcastStates.waiting_text)
        await send_menu(event, context, f"Сегмент: {segment_name} ({len(users)} чел.).\n\nВведите текст сообщения:", broadcast_kb.get_cancel_broadcast_kb())

    @dp.message_created(AdminBroadcastStates.waiting_text, F.message.body.text)
    async def fsm_broadcast_text(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)
        text = event.message.body.text.strip()
        await context.update_data(broadcast_text=text)
        await context.set_state(AdminBroadcastStates.waiting_media)
        await send_menu(
            event, context,
            "Текст принят.\n\nТеперь отправьте файл (картинка, видео, документ) или нажмите кнопку «Без файла».",
            broadcast_kb.get_skip_media_kb(),
        )

    @dp.message_callback(AdminBroadcastStates.waiting_media, F.callback.payload == "brd:skip_media")
    async def fsm_broadcast_skip_media(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await _show_broadcast_preview(event, context, None)

    @dp.message_created(AdminBroadcastStates.waiting_media, F.message.body.attachments)
    async def fsm_broadcast_media(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)
        attachments = event.message.body.attachments
        if not attachments:
            return
            
        attachment = attachments[0]
        payload = getattr(attachment, "payload", None)
        file_url = None
        if payload:
            # В maxapi url может лежать в разных атрибутах в зависимости от типа файла
            file_url = getattr(payload, "url", None) or getattr(payload, "photo_url", None) or getattr(payload, "file_url", None)
            
        if not file_url:
            await send_menu(event, context, "Не удалось получить ссылку на файл. Попробуйте ещё раз.", broadcast_kb.get_skip_media_kb())
            return
            
        media_dir = settings.log_dir.parent / "temp_media"
        media_dir.mkdir(parents=True, exist_ok=True)
        ext = getattr(attachment, "type", "bin") 
        filename = f"broadcast_{int(time.time())}.{ext}"
        save_path = media_dir / filename
        
        await send_menu(event, context, "Файл загружается, пожалуйста подождите...", broadcast_kb.get_cancel_broadcast_kb())
        success = await download_media(file_url, save_path)
        
        if not success:
            await send_menu(event, context, "Ошибка скачивания файла. Попробуйте ещё раз.", broadcast_kb.get_skip_media_kb())
            return
            
        await _show_broadcast_preview(event, context, save_path)

    @dp.message_callback(AdminBroadcastStates.waiting_confirm, F.callback.payload == "brd:confirm_send")
    async def cb_confirm_broadcast(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)
        data = await context.get_data()
        await context.clear()
        
        # Получаем ID диалога администратора для отправки отчёта
        admin_chat_id = await get_event_chat_id(event)
        
        # Запускаем фоновую задачу
        asyncio.create_task(
            send_broadcast_task(
                bot=bot,
                admin_chat_id=admin_chat_id,
                chat_ids=data.get("broadcast_chat_ids", []),
                text=data.get("broadcast_text", ""),
                media_path=data.get("broadcast_media_path"),
                settings=settings,
            )
        )
        
        await send_menu(
            event, context,
            "✅ Рассылка запущена в фоне!\n\n"
            "Отчёт о доставке будет отправлен в этот диалог по завершении.",
            None,
        )
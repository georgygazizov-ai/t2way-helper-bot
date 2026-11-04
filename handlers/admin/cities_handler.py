import logging

from maxapi import Dispatcher, F
from maxapi.types import Command, MessageCreated, MessageCallback
from maxapi.context import MemoryContext

from repositories.macro_region_repo import MacroRegionRepo
from repositories.city_repo import CityRepo
from keyboards.admin import cities_kb
from states.admin_states import MacroRegionStates, CityStates


logger = logging.getLogger(__name__)


async def get_chat_id(event) -> int | None:
    """Универсальный способ получить ID чата из события."""
    if hasattr(event, "message") and hasattr(event.message, "recipient") and event.message.recipient:
        return event.message.recipient.chat_id
    if hasattr(event, "chat_id"):
        return event.chat_id
    try:
        chat = await event.fetch_chat()
        return chat.chat_id if chat else None
    except Exception:
        return None


async def delete_bot_message(event, message_id: int):
    """Пытается удалить сообщение бота по ID."""
    chat_id = await get_chat_id(event)
    if not chat_id:
        return
    try:
        await event.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.debug("Не удалось удалить сообщение %s: %s", message_id, e)


async def clear_last_bot_message(event, context: MemoryContext):
    """Удаляет предыдущее сообщение бота, объект которого сохранен в контексте."""
    data = await context.get_data()
    msg_obj = data.get("last_bot_message_obj")
    
    if msg_obj:
        try:
            # Вызываем метод delete у сохраненного объекта сообщения
            await msg_obj.delete()
        except Exception as e:
            logger.debug("Не удалось удалить сообщение: %s", e)


async def send_and_save(event, context: MemoryContext, text: str, attachments=None):
    """Отправляет сообщение и сохраняет его объект в контексте для будущего удаления."""
    
    # Библиотека maxapi ожидает список вложений.
    if attachments is not None and not isinstance(attachments, list):
        attachments = [attachments]

    msg = await event.message.answer(text, attachments=attachments)
    
    # Реальный объект сообщения (у которого есть метод delete) 
    # находится в атрибуте .message объекта ответа
    if hasattr(msg, 'message'):
        await context.update_data(last_bot_message_obj=msg.message)
    else:
        await context.update_data(last_bot_message_obj=msg)


def register_spravochnik_handlers(
    dp: Dispatcher,
    macro_repo: MacroRegionRepo,
    city_repo: CityRepo,
) -> None:
    
    # === ТОЧКА ВХОДА ===
    @dp.message_created(Command("admin_spravochnik"))
    async def cmd_spravochnik(event: MessageCreated, context: MemoryContext):
        await context.clear()
        await send_and_save(
            event, context,
            "Меню управления справочниками:",
            cities_kb.get_spravochnik_menu_kb()
        )

    # === ГЛАВНОЕ МЕНЮ ===
    @dp.message_callback(F.callback.payload == "spr:main_menu")
    async def cb_main_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await event.message.delete()  # Удаляем сообщение с кнопкой
        await send_and_save(
            event, context,
            "Меню управления справочниками:",
            cities_kb.get_spravochnik_menu_kb()
        )

    # === МАКРОРЕГИОНЫ ===
    
    @dp.message_callback(F.callback.payload == "spr:macro_menu")
    async def cb_macro_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await event.message.delete()
        await send_and_save(
            event, context,
            "Управление макрорегионами:",
            cities_kb.get_macro_actions_kb()
        )

    @dp.message_callback(F.callback.payload == "spr:macro_add")
    async def cb_macro_add_start(event: MessageCallback, context: MemoryContext):
        await event.message.delete()
        await context.set_state(MacroRegionStates.waiting_name)
        await send_and_save(
            event, context,
            "Введите название нового макрорегиона:",
            cities_kb.get_back_kb("spr:macro_menu")
        )

    @dp.message_created(MacroRegionStates.waiting_name, F.message.body.text)
    async def fsm_macro_add_name(event: MessageCreated, context: MemoryContext):
        name = event.message.body.text.strip()
        await clear_last_bot_message(event, context)
        
        if not name:
            await send_and_save(event, context, "Название не может быть пустым. Попробуйте еще раз:")
            return

        try:
            await macro_repo.create(name)
            await context.clear()
            await send_and_save(
                event, context,
                f"✅ Макрорегион '{name}' успешно добавлен!",
                cities_kb.get_macro_actions_kb()
            )
        except Exception as e:
            logger.error("[DB] Ошибка создания макрорегиона: %s", e)
            await context.clear()
            await send_and_save(
                event, context,
                "❌ Ошибка при сохранении. Возможно, такой макрорегион уже существует.",
                cities_kb.get_macro_actions_kb()
            )

    @dp.message_callback(F.callback.payload == "spr:macro_deactivate_list")
    async def cb_macro_deactivate_list(event: MessageCallback, context: MemoryContext):
        regions = await macro_repo.get_all_active()
        await event.message.delete()
        if not regions:
            await send_and_save(
                event, context,
                "Нет активных макрорегионов для деактивации.",
                cities_kb.get_back_kb("spr:macro_menu")
            )
            return
        
        await send_and_save(
            event, context,
            "Выберите макрорегион для деактивации:",
            cities_kb.get_macro_deactivate_list_kb(regions)
        )

    @dp.message_callback(F.callback.payload.startswith("spr:macro_deactivate:"))
    async def cb_macro_deactivate(event: MessageCallback, context: MemoryContext):
        region_id = int(event.callback.payload.split(":")[-1])
        await event.message.delete()
        await macro_repo.deactivate(region_id)
        await context.clear()
        await send_and_save(
            event, context,
            "✅ Макрорегион деактивирован.",
            cities_kb.get_macro_actions_kb()
        )

    # === ГОРОДА ===

    @dp.message_callback(F.callback.payload == "spr:city_menu")
    async def cb_city_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await event.message.delete()
        await send_and_save(
            event, context,
            "Управление городами:",
            cities_kb.get_city_actions_kb()
        )

    @dp.message_callback(F.callback.payload == "spr:city_add_start")
    async def cb_city_add_start(event: MessageCallback, context: MemoryContext):
        regions = await macro_repo.get_all_active()
        await event.message.delete()
        if not regions:
            await send_and_save(
                event, context,
                "Сначала добавьте хотя бы один макрорегион.",
                cities_kb.get_back_kb("spr:city_menu")
            )
            return
        
        await context.set_state(CityStates.waiting_macro_region)
        await send_and_save(
            event, context,
            "Выберите макрорегион для нового города:",
            cities_kb.get_macro_region_choice_kb(regions)
        )

    @dp.message_callback(CityStates.waiting_macro_region, F.callback.payload.startswith("spr:city_choose_macro:"))
    async def fsm_city_choose_macro(event: MessageCallback, context: MemoryContext):
        macro_id = int(event.callback.payload.split(":")[-1])
        await context.update_data(selected_macro_region_id=macro_id)
        await event.message.delete()
        
        await context.set_state(CityStates.waiting_name)
        await send_and_save(
            event, context,
            "Введите название города:",
            cities_kb.get_back_kb("spr:city_menu")
        )

    @dp.message_created(CityStates.waiting_name, F.message.body.text)
    async def fsm_city_add_name(event: MessageCreated, context: MemoryContext):
        name = event.message.body.text.strip()
        await clear_last_bot_message(event, context)
        
        if not name:
            await send_and_save(event, context, "Название не может быть пустым. Попробуйте еще раз:")
            return

        data = await context.get_data()
        macro_id = data.get("selected_macro_region_id")
        if not macro_id:
            await context.clear()
            await send_and_save(
                event, context,
                "Ошибка контекста. Начните сначала.",
                cities_kb.get_city_actions_kb()
            )
            return

        try:
            await city_repo.create(name, macro_id)
            await context.clear()
            await send_and_save(
                event, context,
                f"✅ Город '{name}' успешно добавлен!",
                cities_kb.get_city_actions_kb()
            )
        except Exception as e:
            logger.error("[DB] Ошибка создания города: %s", e)
            await context.clear()
            await send_and_save(
                event, context,
                "❌ Ошибка при сохранении. Возможно, такой город уже существует.",
                cities_kb.get_city_actions_kb()
            )

    @dp.message_callback(F.callback.payload == "spr:city_deactivate_list")
    async def cb_city_deactivate_list(event: MessageCallback, context: MemoryContext):
        cities = await city_repo.get_all_active()
        await event.message.delete()
        if not cities:
            await send_and_save(
                event, context,
                "Нет активных городов для деактивации.",
                cities_kb.get_back_kb("spr:city_menu")
            )
            return
        
        await send_and_save(
            event, context,
            "Выберите город для деактивации:",
            cities_kb.get_city_deactivate_list_kb(cities)
        )

    @dp.message_callback(F.callback.payload.startswith("spr:city_deactivate:"))
    async def cb_city_deactivate(event: MessageCallback, context: MemoryContext):
        city_id = int(event.callback.payload.split(":")[-1])
        await event.message.delete()
        await city_repo.deactivate(city_id)
        await context.clear()
        await send_and_save(
            event, context,
            "✅ Город деактивирован.",
            cities_kb.get_city_actions_kb()
        )
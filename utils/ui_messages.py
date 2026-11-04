import logging

from maxapi.context import MemoryContext


logger = logging.getLogger(__name__)


async def delete_callback_message(event) -> None:
    """
    Удаляет сообщение, на котором была нажата inline-кнопка.
    Это сообщение бота, поэтому удалять можно.
    """

    try:
        await event.message.delete()
    except Exception as error:
        logger.debug("Не удалось удалить callback-сообщение: %s", error)


async def clear_last_bot_message(context: MemoryContext) -> None:
    """
    Удаляет предыдущее сообщение бота, сохранённое в контексте.
    Используется при текстовом вводе в FSM.
    """

    data = await context.get_data()
    message_obj = data.get("last_bot_message_obj")

    if message_obj is None:
        return

    try:
        await message_obj.delete()
    except Exception as error:
        logger.debug("Не удалось удалить предыдущее сообщение бота: %s", error)


async def send_menu(
    event,
    context: MemoryContext,
    text: str,
    keyboard=None,
):
    """
    Отправляет сообщение с inline-клавиатурой и сохраняет объект сообщения.
    Потом это сообщение можно удалить через clear_last_bot_message().
    """

    attachments = None

    if keyboard is not None:
        # maxapi ожидает список вложений.
        attachments = keyboard if isinstance(keyboard, list) else [keyboard]

    sent = await event.message.answer(text, attachments=attachments)

    # В maxapi реальный объект сообщения лежит в sent.message.
    message_obj = getattr(sent, "message", sent)

    await context.update_data(last_bot_message_obj=message_obj)

    return message_obj
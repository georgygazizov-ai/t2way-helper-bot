from maxapi import Dispatcher
from maxapi.types import Command, MessageCreated


def register_system_handlers(dp: Dispatcher) -> None:
    """
    Системные команды бота.
    """

    @dp.message_created(Command("help"))
    async def help_handler(event: MessageCreated) -> None:
        await event.message.answer(
            "Доступные команды:\n\n"
            "/start — регистрация в боте\n"
            "/profile — мой профиль\n"
            "/help — справка\n"
            "/ping — проверка связи с ботом"
        )

    @dp.message_created(Command("ping"))
    async def ping_handler(event: MessageCreated) -> None:
        await event.message.answer("pong")
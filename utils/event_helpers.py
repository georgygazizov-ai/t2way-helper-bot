# Вспомогательные функции для работы с событиями MAX.
# Нужны, чтобы не дублировать один и тот же код в разных обработчиках.


async def get_event_user_id(event_object) -> int | None:
    """
    Пытается получить ID пользователя из события.

    В разных типах событий пользователь может лежать в разных местах,
    поэтому проверяем несколько вариантов.
    """

    fetch_from_user = getattr(event_object, "fetch_from_user", None)

    if callable(fetch_from_user):
        user = await fetch_from_user()
    else:
        user = getattr(event_object, "from_user", None)

    if user is None:
        return None

    return getattr(user, "user_id", None)


def get_event_text(event_object) -> str | None:
    """
    Пытается получить текст сообщения из события.
    Возвращает None, если события с текстом нет.
    """

    message = getattr(event_object, "message", None)

    if message is None:
        return None

    body = getattr(message, "body", None)

    if body is None:
        return None

    text = getattr(body, "text", None)

    if not text:
        return None

    return text.strip()


async def answer_event(event_object, text: str) -> bool:
    """
    Универсальный ответ на событие.

    Если это обычное сообщение — отвечаем в чат.
    Если это callback от кнопки — стараемся отредактировать сообщение.
    """

    message = getattr(event_object, "message", None)

    if message is not None and hasattr(message, "answer"):
        await message.answer(text)
        return True

    answer = getattr(event_object, "answer", None)

    if callable(answer):
        try:
            await answer(new_text=text)
            return True
        except TypeError:
            # На случай, если конкретный тип события принимает только текст.
            await answer(text)
            return True
        except Exception:
            return False

    return False

async def get_event_chat_id(event_object) -> int | None:
    """
    Возвращает ID чата, в котором произошло событие.

    Для личного диалога это ID диалога,
    который в MAX не совпадает с ID пользователя.
    """

    message = getattr(event_object, "message", None)

    if message is not None:
        recipient = getattr(message, "recipient", None)

        if recipient is not None:
            chat_id = getattr(recipient, "chat_id", None)

            if chat_id is not None:
                return chat_id

    fetch_chat = getattr(event_object, "fetch_chat", None)

    if callable(fetch_chat):
        chat = await fetch_chat()

        if chat is not None:
            return getattr(chat, "chat_id", None)

    return getattr(event_object, "chat_id", None)
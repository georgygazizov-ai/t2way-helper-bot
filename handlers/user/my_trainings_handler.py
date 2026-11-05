import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import MessageCallback, MessageCreated

from keyboards.user import trainings_kb
from repositories.city_repo import CityRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.training_repo import TrainingRepo
from services.training_service import (
    format_lead_name,
    format_training_card,
    format_training_date,
)
from utils.time_utils import today_str_in_tz
from utils.ui_messages import delete_callback_message, send_menu


logger = logging.getLogger(__name__)


def register_my_trainings_handlers(
    dp: Dispatcher,
    training_repo: TrainingRepo,
    city_repo: CityRepo,
    macro_repo: MacroRegionRepo,
    timezone_name: str,
) -> None:
    """
    Пользовательский просмотр тренингов:
    мои предстоящие, мои проведённые, календарь команды.
    """

    async def build_list_items(trainings) -> list:
        """
        Собирает пары (ID тренинга, текст кнопки).
        """

        items = []

        for training in trainings:
            city = await city_repo.get_by_id(training["city_id"])
            city_name = city.name if city else "—"

            items.append(
                (
                    training["id"],
                    f"{format_training_date(training['date'])} | "
                    f"{training['format']} | {city_name}",
                )
            )

        return items

    async def send_list(event, context, trainings, title: str, empty_text: str):
        """
        Показывает список тренингов или сообщение, что списка нет.
        """

        if not trainings:
            await send_menu(
                event,
                context,
                empty_text,
                trainings_kb.get_my_trainings_menu_kb(),
            )
            return

        items = await build_list_items(trainings)

        await send_menu(
            event,
            context,
            title,
            trainings_kb.get_trainings_list_kb(items),
        )

    # === МЕНЮ ===

    @dp.message_created(F.message.body.text == "/my_trainings")
    async def cmd_my_trainings(event: MessageCreated, context: MemoryContext):
        await context.clear()

        await send_menu(
            event,
            context,
            "Тренинги:",
            trainings_kb.get_my_trainings_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "mytrain:menu")
    async def cb_my_trainings_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Тренинги:",
            trainings_kb.get_my_trainings_menu_kb(),
        )

    # === СПИСКИ ===

    @dp.message_callback(F.callback.payload == "mytrain:my_upcoming")
    async def cb_my_upcoming(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)

        today = today_str_in_tz(timezone_name)

        trainings = await training_repo.get_upcoming_for_user(
            current_user.user_id,
            today,
        )

        await send_list(
            event,
            context,
            trainings,
            "Мои предстоящие тренинги:",
            "У вас нет предстоящих тренингов.",
        )

    @dp.message_callback(F.callback.payload == "mytrain:my_done")
    async def cb_my_done(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)

        trainings = await training_repo.get_conducted_for_user(current_user.user_id)

        await send_list(
            event,
            context,
            trainings,
            "Мои проведённые тренинги:",
            "У вас ещё нет проведённых тренингов.",
        )

    @dp.message_callback(F.callback.payload == "mytrain:team")
    async def cb_team_calendar(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        today = today_str_in_tz(timezone_name)

        trainings = await training_repo.get_upcoming_all(today)

        await send_list(
            event,
            context,
            trainings,
            "Календарь команды: предстоящие тренинги:",
            "В календаре пока нет предстоящих тренингов.",
        )

    # === КАРТОЧКА ТРЕНИНГА ===

    @dp.message_callback(F.callback.payload.startswith("mytrain:view:"))
    async def cb_view_training(event: MessageCallback, context: MemoryContext):
        training_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        training = await training_repo.get_by_id(training_id)

        if training is None:
            await send_menu(
                event,
                context,
                "Тренинг не найден.",
                trainings_kb.get_my_trainings_menu_kb(),
            )
            return

        city = await city_repo.get_by_id(training["city_id"])
        city_name = city.name if city else "—"

        macro = None
        if city is not None:
            macro = await macro_repo.get_by_id(city.macro_region_id)
        macro_name = macro.name if macro else "—"

        leads = await training_repo.get_leads(training_id)
        leads_names = ", ".join(format_lead_name(lead) for lead in leads) or "не назначены"

        text = format_training_card(training, city_name, macro_name, leads_names)

        await send_menu(
            event,
            context,
            text,
            trainings_kb.get_training_card_kb(),
        )
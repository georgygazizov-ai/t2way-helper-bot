import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from keyboards.admin import trainings_kb
from repositories.city_repo import CityRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.training_repo import TrainingRepo
from repositories.user_repo import UserRepo
from services.training_service import (
    format_lead_name,
    format_training_date,
    parse_training_date,
)
from states.admin_states import AdminTrainingEditStates, AdminTrainingStates
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu


logger = logging.getLogger(__name__)


def register_trainings_handlers(
    dp: Dispatcher,
    bot,
    training_repo: TrainingRepo,
    user_repo: UserRepo,
    city_repo: CityRepo,
    macro_repo: MacroRegionRepo,
) -> None:
    """
    Управление тренингами: создание, редактирование, просмотр.
    """

    # === МЕНЮ ===

    @dp.message_created(Command("admin_trainings"))
    async def cmd_trainings(event: MessageCreated, context: MemoryContext):
        await context.clear()

        await send_menu(
            event,
            context,
            "Управление тренингами:",
            trainings_kb.get_trainings_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "train:menu")
    async def cb_trainings_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Управление тренингами:",
            trainings_kb.get_trainings_menu_kb(),
        )

    # === СОЗДАНИЕ ТРЕНИНГА ===

    @dp.message_callback(F.callback.payload == "train:create")
    async def cb_create_start(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.set_state(AdminTrainingStates.waiting_date)

        await send_menu(
            event,
            context,
            "Введите дату тренинга в формате ДД.ММ.ГГГГ:",
            trainings_kb.get_cancel_kb(),
        )

    @dp.message_created(AdminTrainingStates.waiting_date, F.message.body.text)
    async def fsm_date(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        try:
            date_str = parse_training_date(event.message.body.text)
        except ValueError as error:
            await send_menu(
                event,
                context,
                f"{error}\n\nВведите дату ещё раз:",
                trainings_kb.get_cancel_kb(),
            )
            return

        await context.update_data(date=date_str)
        await context.set_state(AdminTrainingStates.waiting_format)

        await send_menu(
            event,
            context,
            "Выберите формат тренинга:",
            trainings_kb.get_format_choice_kb(),
        )

    @dp.message_callback(AdminTrainingStates.waiting_format, F.callback.payload.startswith("train:format:"))
    async def fsm_format(event: MessageCallback, context: MemoryContext):
        format_type = event.callback.payload.split(":")[-1]
        await delete_callback_message(event)

        await context.update_data(format=format_type)

        macro_regions = await macro_repo.get_all_active()

        if not macro_regions:
            await context.clear()
            await send_menu(
                event,
                context,
                "Нет активных макрорегионов. Сначала добавьте макрорегион через /admin_spravochnik.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await context.set_state(AdminTrainingStates.waiting_macro_region)

        await send_menu(
            event,
            context,
            "Выберите макрорегион:",
            trainings_kb.get_macro_region_choice_kb(macro_regions),
        )

    @dp.message_callback(
        AdminTrainingStates.waiting_macro_region,
        F.callback.payload.startswith("train:macro:"),
    )
    async def fsm_macro_region(event: MessageCallback, context: MemoryContext):
        macro_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        cities = await city_repo.get_active_by_macro_region(macro_id)

        if not cities:
            macro_regions = await macro_repo.get_all_active()
            await send_menu(
                event,
                context,
                "В этом макрорегионе нет активных городов. Выберите другой макрорегион:",
                trainings_kb.get_macro_region_choice_kb(macro_regions),
            )
            return

        await context.update_data(macro_region_id=macro_id)
        await context.set_state(AdminTrainingStates.waiting_city)

        await send_menu(
            event,
            context,
            "Выберите город:",
            trainings_kb.get_city_choice_kb(cities),
        )

    @dp.message_callback(F.callback.payload == "train:macro_back")
    async def cb_macro_back(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        macro_regions = await macro_repo.get_all_active()
        await context.set_state(AdminTrainingStates.waiting_macro_region)

        await send_menu(
            event,
            context,
            "Выберите макрорегион:",
            trainings_kb.get_macro_region_choice_kb(macro_regions),
        )

    @dp.message_callback(
        AdminTrainingStates.waiting_city,
        F.callback.payload.startswith("train:city:"),
    )
    async def fsm_city(event: MessageCallback, context: MemoryContext):
        city_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        await context.update_data(city_id=city_id)

        trainers = await user_repo.get_all_trainers()

        if not trainers:
            await context.clear()
            await send_menu(
                event,
                context,
                "Нет доступных тренеров. Сначала зарегистрируйте тренеров.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await context.update_data(selected_leads=[])
        await context.set_state(AdminTrainingStates.waiting_leads)

        await send_menu(
            event,
            context,
            "Выберите ведущих тренинга (от 1 до 3 человек):",
            trainings_kb.get_leads_choice_kb(trainers, []),
        )

    @dp.message_callback(
        AdminTrainingStates.waiting_leads,
        F.callback.payload.startswith("train:lead_toggle:"),
    )
    async def fsm_lead_toggle(event: MessageCallback, context: MemoryContext):
        lead_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        data = await context.get_data()
        selected = list(data.get("selected_leads", []))

        if lead_id in selected:
            selected.remove(lead_id)
        else:
            if len(selected) >= 3:
                await send_menu(
                    event,
                    context,
                    "Максимум 3 ведущих. Сначала уберите одного.",
                    trainings_kb.get_cancel_kb(),
                )
                return

            selected.append(lead_id)

        await context.update_data(selected_leads=selected)

        trainers = await user_repo.get_all_trainers()

        await send_menu(
            event,
            context,
            "Выберите ведущих тренинга (от 1 до 3 человек):",
            trainings_kb.get_leads_choice_kb(trainers, selected),
        )

    @dp.message_callback(AdminTrainingStates.waiting_leads, F.callback.payload == "train:leads_confirm")
    async def fsm_leads_confirm(event: MessageCallback, context: MemoryContext, current_user):
        await delete_callback_message(event)

        data = await context.get_data()
        selected = data.get("selected_leads", [])

        if len(selected) < 1:
            await send_menu(
                event,
                context,
                "Нужно выбрать хотя бы одного ведущего.",
                trainings_kb.get_cancel_kb(),
            )
            return

        # Создаём тренинг
        training_id = await training_repo.create(
            date=data["date"],
            format_type=data["format"],
            city_id=data["city_id"],
            created_by=current_user.user_id,
        )

        # Назначаем ведущих
        for lead_id in selected:
            await training_repo.assign_lead(training_id, lead_id)

        await context.clear()

        logger.info("[AUDIT] Создан тренинг %s", training_id)

        await send_menu(
            event,
            context,
            f"Тренинг ID {training_id} успешно создан.",
            trainings_kb.get_trainings_menu_kb(),
        )

    # === ПРОСМОТР СПИСКА ТРЕНИНГОВ ===

    @dp.message_callback(F.callback.payload == "train:list_all")
    async def cb_list_all(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        trainings = await training_repo.get_all_trainings()

        if not trainings:
            await send_menu(
                event,
                context,
                "Тренингов ещё нет.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await send_menu(
            event,
            context,
            "Все тренинги:",
            trainings_kb.get_trainings_list_kb(trainings),
        )

    @dp.message_callback(F.callback.payload == "train:list_assigned")
    async def cb_list_assigned(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        trainings = await training_repo.get_all_trainings(status_filter="assigned")

        if not trainings:
            await send_menu(
                event,
                context,
                "Назначенных тренингов нет.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await send_menu(
            event,
            context,
            "Назначенные тренинги:",
            trainings_kb.get_trainings_list_kb(trainings),
        )

    # === ПРОСМОТР ТРЕНИНГА ===

    @dp.message_callback(F.callback.payload.startswith("train:view:"))
    async def cb_view_training(event: MessageCallback, context: MemoryContext):
        training_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        training = await training_repo.get_by_id(training_id)

        if training is None:
            await send_menu(
                event,
                context,
                "Тренинг не найден.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        leads = await training_repo.get_leads(training_id)
        leads_text = ", ".join(format_lead_name(lead) for lead in leads) or "не назначены"

        city = await city_repo.get_by_id(training["city_id"])
        city_name = city.name if city else "неизвестный"

        text = (
            f"Тренинг ID {training_id}\n\n"
            f"Дата: {format_training_date(training['date'])}\n"
            f"Формат: {training['format']}\n"
            f"Город: {city_name}\n"
            f"Ведущие: {leads_text}\n"
            f"Статус: {training['status']}"
        )

        await send_menu(
            event,
            context,
            text,
            trainings_kb.get_training_view_kb(training_id, training["status"]),
        )

    # === РЕДАКТИРОВАНИЕ ТРЕНИНГА ===

    @dp.message_callback(F.callback.payload.startswith("train:edit:"))
    async def cb_edit_training(event: MessageCallback, context: MemoryContext):
        training_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        training = await training_repo.get_by_id(training_id)

        if training is None:
            await send_menu(
                event,
                context,
                "Тренинг не найден.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        if training["status"] != "assigned":
            await send_menu(
                event,
                context,
                "Можно редактировать только назначенные тренинги.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await context.update_data(edit_training_id=training_id)

        await send_menu(
            event,
            context,
            f"Редактирование тренинга ID {training_id}:",
            trainings_kb.get_training_edit_kb(training_id),
        )

    @dp.message_callback(F.callback.payload.startswith("train:edit_date:"))
    async def cb_edit_date_start(event: MessageCallback, context: MemoryContext):
        training_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        await context.update_data(edit_training_id=training_id)
        await context.set_state(AdminTrainingEditStates.waiting_date)

        await send_menu(
            event,
            context,
            "Введите новую дату в формате ДД.ММ.ГГГГ:",
            trainings_kb.get_cancel_kb(),
        )

    @dp.message_created(AdminTrainingEditStates.waiting_date, F.message.body.text)
    async def fsm_edit_date(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        try:
            date_str = parse_training_date(event.message.body.text)
        except ValueError as error:
            await send_menu(
                event,
                context,
                f"{error}\n\nВведите дату ещё раз:",
                trainings_kb.get_cancel_kb(),
            )
            return

        data = await context.get_data()
        training_id = data.get("edit_training_id")

        if not training_id:
            await context.clear()
            await send_menu(
                event,
                context,
                "Ошибка контекста.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await training_repo.update_training(training_id, date=date_str)
        await context.clear()

        logger.info("[AUDIT] Изменена дата тренинга %s", training_id)

        await send_menu(
            event,
            context,
            "Дата тренинга обновлена.",
            trainings_kb.get_trainings_menu_kb(),
        )

    @dp.message_callback(F.callback.payload.startswith("train:edit_format:"))
    async def cb_edit_format_start(event: MessageCallback, context: MemoryContext):
        training_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        await context.update_data(edit_training_id=training_id)

        await send_menu(
            event,
            context,
            "Выберите новый формат:",
            trainings_kb.get_format_choice_kb(),
        )

    @dp.message_callback(F.callback.payload.startswith("train:format:"))
    async def fsm_edit_format(event: MessageCallback, context: MemoryContext):
        format_type = event.callback.payload.split(":")[-1]
        await delete_callback_message(event)

        data = await context.get_data()
        training_id = data.get("edit_training_id")

        if not training_id:
            await context.clear()
            await send_menu(
                event,
                context,
                "Ошибка контекста.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await training_repo.update_training(training_id, format_type=format_type)
        await context.clear()

        logger.info("[AUDIT] Изменён формат тренинга %s", training_id)

        await send_menu(
            event,
            context,
            "Формат тренинга обновлён.",
            trainings_kb.get_trainings_menu_kb(),
        )

    @dp.message_callback(F.callback.payload.startswith("train:edit_city:"))
    async def cb_edit_city_start(event: MessageCallback, context: MemoryContext):
        training_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        await context.update_data(edit_training_id=training_id)

        macro_regions = await macro_repo.get_all_active()

        if not macro_regions:
            await context.clear()
            await send_menu(
                event,
                context,
                "Нет активных макрорегионов.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await context.set_state(AdminTrainingEditStates.waiting_city_macro)

        await send_menu(
            event,
            context,
            "Выберите макрорегион:",
            trainings_kb.get_macro_region_choice_kb(macro_regions),
        )

    @dp.message_callback(
        AdminTrainingEditStates.waiting_city_macro,
        F.callback.payload.startswith("train:macro:"),
    )
    async def fsm_edit_city_macro(event: MessageCallback, context: MemoryContext):
        macro_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        cities = await city_repo.get_active_by_macro_region(macro_id)

        if not cities:
            macro_regions = await macro_repo.get_all_active()
            await send_menu(
                event,
                context,
                "В этом макрорегионе нет активных городов. Выберите другой макрорегион:",
                trainings_kb.get_macro_region_choice_kb(macro_regions),
            )
            return

        await context.update_data(edit_macro_region_id=macro_id)
        await context.set_state(AdminTrainingEditStates.waiting_city)

        await send_menu(
            event,
            context,
            "Выберите город:",
            trainings_kb.get_city_choice_kb(cities),
        )

    @dp.message_callback(
        AdminTrainingEditStates.waiting_city,
        F.callback.payload.startswith("train:city:"),
    )
    async def fsm_edit_city(event: MessageCallback, context: MemoryContext):
        city_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        data = await context.get_data()
        training_id = data.get("edit_training_id")

        if not training_id:
            await context.clear()
            await send_menu(
                event,
                context,
                "Ошибка контекста.",
                trainings_kb.get_trainings_menu_kb(),
            )
            return

        await training_repo.update_training(training_id, city_id=city_id)
        await context.clear()

        logger.info("[AUDIT] Изменён город тренинга %s", training_id)

        await send_menu(
            event,
            context,
            "Город тренинга обновлён.",
            trainings_kb.get_trainings_menu_kb(),
        )
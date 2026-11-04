import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import MessageCallback, MessageCreated

from keyboards.user import profile_kb
from repositories.city_repo import CityRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.user_repo import UserRepo
from services.profile_service import format_profile_for_user
from states.user_states import UserProfileEditStates
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu
from utils.validators import parse_birth_date, validate_text_field


logger = logging.getLogger(__name__)


async def show_profile_card(
    event,
    context: MemoryContext,
    user_repo: UserRepo,
    city_repo: CityRepo,
    user_id: int,
    note: str | None = None,
) -> None:
    """
    Показывает карточку профиля с актуальными данными из БД.

    Если передан note, он выводится сверху карточки
    (например, «Должность обновлена.»).
    """

    user = await user_repo.get_by_id(user_id)

    if user is None:
        await send_menu(event, context, "Профиль не найден.", None)
        return

    city = None
    if user.city_id:
        city = await city_repo.get_by_id(user.city_id)

    text = format_profile_for_user(user, city.name if city else None)

    if note:
        text = f"{note}\n\n{text}"

    await send_menu(
        event,
        context,
        text,
        profile_kb.get_user_profile_menu_kb(),
    )


def register_user_profile_handlers(
    dp: Dispatcher,
    user_repo: UserRepo,
    city_repo: CityRepo,
    macro_repo: MacroRegionRepo,
) -> None:
    """
    Пользовательский профиль: просмотр и редактирование разрешённых полей.
    """

    @dp.message_created(F.message.body.text == "/profile")
    async def cmd_profile(event: MessageCreated, context: MemoryContext, current_user):
        await context.clear()

        await show_profile_card(
            event,
            context,
            user_repo,
            city_repo,
            current_user.user_id,
        )

    @dp.message_callback(F.callback.payload == "up:menu")
    async def cb_profile_menu(event: MessageCallback, context: MemoryContext, current_user):
        await context.clear()
        await delete_callback_message(event)

        await show_profile_card(
            event,
            context,
            user_repo,
            city_repo,
            current_user.user_id,
        )

    @dp.message_callback(F.callback.payload == "up:close")
    async def cb_profile_close(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Профиль закрыт.",
            None,
        )

    # === ИЗМЕНЕНИЕ ДОЛЖНОСТИ ===

    @dp.message_callback(F.callback.payload == "up:edit_position")
    async def cb_edit_position(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.set_state(UserProfileEditStates.waiting_position)

        await send_menu(
            event,
            context,
            "Введите новую должность:",
            profile_kb.get_cancel_kb(),
        )

    @dp.message_created(UserProfileEditStates.waiting_position, F.message.body.text)
    async def fsm_position(event: MessageCreated, context: MemoryContext, current_user):
        await clear_last_bot_message(context)

        try:
            position = validate_text_field(event.message.body.text, "Должность")
        except ValueError as error:
            await send_menu(
                event,
                context,
                f"{error}\n\nВведите должность ещё раз:",
                profile_kb.get_cancel_kb(),
            )
            return

        user = await user_repo.get_by_id(current_user.user_id)

        if user is None:
            await context.clear()
            return

        await user_repo.update_profile(
            user_id=user.user_id,
            last_name=user.last_name,
            first_name=user.first_name,
            patronymic=user.patronymic,
            position=position,
            city_id=user.city_id,
            birth_day=user.birth_day,
            birth_month=user.birth_month,
            birth_year=user.birth_year,
        )

        await context.clear()

        logger.info("[AUDIT] Пользователь %s обновил должность", user.user_id)

        await show_profile_card(
            event,
            context,
            user_repo,
            city_repo,
            user.user_id,
            note="Должность обновлена.",
        )

    # === ИЗМЕНЕНИЕ ГОРОДА ===

    @dp.message_callback(F.callback.payload == "up:edit_city")
    async def cb_edit_city(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        macro_regions = await macro_repo.get_all_active()

        if not macro_regions:
            await send_menu(
                event,
                context,
                "Нет доступных макрорегионов. Обратитесь к администратору.",
                profile_kb.get_user_profile_menu_kb(),
            )
            return

        await context.set_state(UserProfileEditStates.waiting_macro_region)

        await send_menu(
            event,
            context,
            "Выберите макрорегион:",
            profile_kb.get_macro_region_choice_kb(macro_regions),
        )

    @dp.message_callback(
        UserProfileEditStates.waiting_macro_region,
        F.callback.payload.startswith("up:macro:"),
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
                "В этом макрорегионе нет доступных городов. Выберите другой макрорегион:",
                profile_kb.get_macro_region_choice_kb(macro_regions),
            )
            return

        await context.update_data(macro_region_id=macro_id)
        await context.set_state(UserProfileEditStates.waiting_city)

        await send_menu(
            event,
            context,
            "Выберите город:",
            profile_kb.get_city_choice_kb(cities),
        )

    @dp.message_callback(F.callback.payload == "up:macro_back")
    async def cb_macro_back(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        macro_regions = await macro_repo.get_all_active()

        await context.set_state(UserProfileEditStates.waiting_macro_region)

        await send_menu(
            event,
            context,
            "Выберите макрорегион:",
            profile_kb.get_macro_region_choice_kb(macro_regions),
        )

    @dp.message_callback(
        UserProfileEditStates.waiting_city,
        F.callback.payload.startswith("up:city:"),
    )
    async def fsm_city(event: MessageCallback, context: MemoryContext, current_user):
        city_id = int(event.callback.payload.split(":")[-1])
        await delete_callback_message(event)

        user = await user_repo.get_by_id(current_user.user_id)

        if user is None:
            await context.clear()
            return

        await user_repo.update_profile(
            user_id=user.user_id,
            last_name=user.last_name,
            first_name=user.first_name,
            patronymic=user.patronymic,
            position=user.position,
            city_id=city_id,
            birth_day=user.birth_day,
            birth_month=user.birth_month,
            birth_year=user.birth_year,
        )

        await context.clear()

        logger.info("[AUDIT] Пользователь %s обновил город", user.user_id)

        await show_profile_card(
            event,
            context,
            user_repo,
            city_repo,
            user.user_id,
            note="Город обновлён.",
        )

    # === ИЗМЕНЕНИЕ ДАТЫ РОЖДЕНИЯ ===

    @dp.message_callback(F.callback.payload == "up:edit_birth")
    async def cb_edit_birth(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await context.set_state(UserProfileEditStates.waiting_birth_date)

        await send_menu(
            event,
            context,
            "Введите дату рождения в формате ДД.ММ.ГГГГ или ДД.ММ:",
            profile_kb.get_cancel_kb(),
        )

    @dp.message_created(UserProfileEditStates.waiting_birth_date, F.message.body.text)
    async def fsm_birth_date(event: MessageCreated, context: MemoryContext, current_user):
        await clear_last_bot_message(context)

        try:
            birth_day, birth_month, birth_year = parse_birth_date(event.message.body.text)
        except ValueError as error:
            await send_menu(
                event,
                context,
                f"{error}\n\nВведите дату рождения ещё раз:",
                profile_kb.get_cancel_kb(),
            )
            return

        user = await user_repo.get_by_id(current_user.user_id)

        if user is None:
            await context.clear()
            return

        await user_repo.update_profile(
            user_id=user.user_id,
            last_name=user.last_name,
            first_name=user.first_name,
            patronymic=user.patronymic,
            position=user.position,
            city_id=user.city_id,
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
        )

        await context.clear()

        logger.info("[AUDIT] Пользователь %s обновил дату рождения", user.user_id)

        await show_profile_card(
            event,
            context,
            user_repo,
            city_repo,
            user.user_id,
            note="Дата рождения обновлена.",
        )
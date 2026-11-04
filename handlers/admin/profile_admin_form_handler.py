import logging

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import MessageCallback, MessageCreated

from keyboards.admin import profile_admin_kb
from repositories.city_repo import CityRepo
from repositories.macro_region_repo import MacroRegionRepo
from repositories.user_repo import UserRepo
from services.profile_service import format_birth_date, format_user_card
from states.admin_states import AdminProfileFormStates
from utils.ui_messages import clear_last_bot_message, delete_callback_message, send_menu
from utils.validators import parse_birth_date, validate_text_field


logger = logging.getLogger(__name__)


async def start_edit_form(event, context: MemoryContext, target_user) -> None:
    """
    Запускает форму редактирования карточки с шага фамилии.
    Сразу показывает текущее значение фамилии.
    """

    await context.clear()
    await context.update_data(target_user_id=target_user.user_id)
    await context.set_state(AdminProfileFormStates.waiting_last_name)

    await send_menu(
        event,
        context,
        f"Редактируем карточку пользователя ID {target_user.user_id}.\n\n"
        "Введите фамилию:\n\n"
        f"Текущее значение: {target_user.last_name or 'не заполнено'}",
        profile_admin_kb.get_profile_form_step_kb(),
    )


def register_profile_admin_form_handlers(
    dp: Dispatcher,
    bot,
    user_repo: UserRepo,
    city_repo: CityRepo,
    macro_repo: MacroRegionRepo,
) -> None:
    """
    Форма редактирования карточки пользователя администратором.

    На каждом шаге показывается текущее значение поля
    и есть кнопка «Оставить как есть».
    """

    async def get_target_user(context: MemoryContext):
        """Возвращает пользователя, чью карточку редактируем."""

        data = await context.get_data()
        target_user_id = data.get("target_user_id")

        if target_user_id is None:
            return None

        return await user_repo.get_by_id(target_user_id)

    def with_current(prompt: str, current_value: str | None) -> str:
        """Добавляет к вопросу текущее значение поля."""

        if current_value:
            return f"{prompt}\n\nТекущее значение: {current_value}"

        return f"{prompt}\n\nТекущее значение: не заполнено"

    async def current_city_name(user) -> str | None:
        """Возвращает название текущего города пользователя."""

        if user is None or user.city_id is None:
            return None

        city = await city_repo.get_by_id(user.city_id)
        return city.name if city else None

    async def prompt_step(
        event,
        context: MemoryContext,
        prompt: str,
        current_value: str | None,
    ):
        """Показывает шаг текстового ввода с текущим значением."""

        await send_menu(
            event,
            context,
            with_current(prompt, current_value),
            profile_admin_kb.get_profile_form_step_kb(),
        )

    async def go_macro_step(event, context: MemoryContext):
        """Переход к шагу выбора макрорегиона."""

        macro_regions = await macro_repo.get_all_active()

        if not macro_regions:
            await context.clear()
            await send_menu(
                event,
                context,
                "Нет активных макрорегионов. Сначала добавьте макрорегион через /admin_spravochnik.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        user = await get_target_user(context)
        city_name = await current_city_name(user)

        await context.set_state(AdminProfileFormStates.waiting_macro_region)
        await send_menu(
            event,
            context,
            with_current("Выберите макрорегион:", city_name),
            profile_admin_kb.get_macro_region_choice_kb(macro_regions),
        )

    async def go_birth_step(event, context: MemoryContext):
        """Переход к шагу даты рождения."""

        user = await get_target_user(context)

        birth = format_birth_date(user) if user else "не указана"
        birth_value = None if birth == "не указана" else birth

        await context.set_state(AdminProfileFormStates.waiting_birth_date)
        await send_menu(
            event,
            context,
            with_current(
                "Введите дату рождения в формате ДД.ММ.ГГГГ или ДД.ММ:",
                birth_value,
            ),
            profile_admin_kb.get_profile_form_step_kb(),
        )

    async def save_profile(
        event,
        context: MemoryContext,
        birth_day,
        birth_month,
        birth_year,
    ):
        """Сохраняет карточку и показывает результат."""

        data = await context.get_data()
        target_user_id = data.get("target_user_id")

        if not target_user_id:
            await context.clear()
            await send_menu(
                event,
                context,
                "Ошибка контекста. Начните редактирование заново.",
                profile_admin_kb.get_profile_admin_menu_kb(),
            )
            return

        await user_repo.update_profile(
            user_id=target_user_id,
            last_name=data["last_name"],
            first_name=data["first_name"],
            patronymic=data["patronymic"],
            position=data["position"],
            city_id=data["city_id"],
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
        )

        updated_user = await user_repo.get_by_id(target_user_id)
        city = await city_repo.get_by_id(data["city_id"])

        await context.clear()

        logger.info("[AUDIT] Обновлена карточка пользователя %s", target_user_id)

        if updated_user.chat_id is None:
            logger.warning(
                "[ERROR] Пользователь %s ещё не открывал диалог с ботом — уведомление не отправлено",
                target_user_id,
            )
        else:
            try:
                await bot.send_message(
                    chat_id=updated_user.chat_id,
                    text="Ваша карточка в боте обновлена администратором.",
                )
            except Exception as exc:
                logger.warning(
                    "[ERROR] Не удалось уведомить пользователя %s об обновлении профиля: %r",
                    target_user_id,
                    exc,
                )

        await send_menu(
            event,
            context,
            "Карточка сохранена.\n\n"
            + format_user_card(updated_user, city.name if city else None),
            profile_admin_kb.get_profile_admin_menu_kb(),
        )

    # === ШАГ 1. ФАМИЛИЯ ===

    @dp.message_created(AdminProfileFormStates.waiting_last_name, F.message.body.text)
    async def fsm_last_name(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        user = await get_target_user(context)

        try:
            last_name = validate_text_field(event.message.body.text, "Фамилия")
        except ValueError as error:
            await prompt_step(
                event,
                context,
                f"{error}\n\nВведите фамилию ещё раз:",
                user.last_name if user else None,
            )
            return

        await context.update_data(last_name=last_name)
        await context.set_state(AdminProfileFormStates.waiting_first_name)

        await prompt_step(
            event,
            context,
            "Введите имя:",
            user.first_name if user else None,
        )

    @dp.message_callback(AdminProfileFormStates.waiting_last_name, F.callback.payload == "prof:keep")
    async def keep_last_name(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        user = await get_target_user(context)

        if user is None or not user.last_name:
            await prompt_step(event, context, "Текущее значение не заполнено. Введите фамилию:", None)
            return

        await context.update_data(last_name=user.last_name)
        await context.set_state(AdminProfileFormStates.waiting_first_name)

        await prompt_step(
            event,
            context,
            "Введите имя:",
            user.first_name,
        )

    # === ШАГ 2. ИМЯ ===

    @dp.message_created(AdminProfileFormStates.waiting_first_name, F.message.body.text)
    async def fsm_first_name(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        user = await get_target_user(context)

        try:
            first_name = validate_text_field(event.message.body.text, "Имя")
        except ValueError as error:
            await prompt_step(
                event,
                context,
                f"{error}\n\nВведите имя ещё раз:",
                user.first_name if user else None,
            )
            return

        await context.update_data(first_name=first_name)
        await context.set_state(AdminProfileFormStates.waiting_patronymic)

        await prompt_step(
            event,
            context,
            "Введите отчество:",
            user.patronymic if user else None,
        )

    @dp.message_callback(AdminProfileFormStates.waiting_first_name, F.callback.payload == "prof:keep")
    async def keep_first_name(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        user = await get_target_user(context)

        if user is None or not user.first_name:
            await prompt_step(event, context, "Текущее значение не заполнено. Введите имя:", None)
            return

        await context.update_data(first_name=user.first_name)
        await context.set_state(AdminProfileFormStates.waiting_patronymic)

        await prompt_step(
            event,
            context,
            "Введите отчество:",
            user.patronymic,
        )

    # === ШАГ 3. ОТЧЕСТВО ===

    @dp.message_created(AdminProfileFormStates.waiting_patronymic, F.message.body.text)
    async def fsm_patronymic(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        user = await get_target_user(context)

        try:
            patronymic = validate_text_field(event.message.body.text, "Отчество")
        except ValueError as error:
            await prompt_step(
                event,
                context,
                f"{error}\n\nВведите отчество ещё раз:",
                user.patronymic if user else None,
            )
            return

        await context.update_data(patronymic=patronymic)
        await context.set_state(AdminProfileFormStates.waiting_position)

        await prompt_step(
            event,
            context,
            "Введите должность:",
            user.position if user else None,
        )

    @dp.message_callback(AdminProfileFormStates.waiting_patronymic, F.callback.payload == "prof:keep")
    async def keep_patronymic(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        user = await get_target_user(context)

        if user is None or not user.patronymic:
            await prompt_step(event, context, "Текущее значение не заполнено. Введите отчество:", None)
            return

        await context.update_data(patronymic=user.patronymic)
        await context.set_state(AdminProfileFormStates.waiting_position)

        await prompt_step(
            event,
            context,
            "Введите должность:",
            user.position,
        )

    # === ШАГ 4. ДОЛЖНОСТЬ ===

    @dp.message_created(AdminProfileFormStates.waiting_position, F.message.body.text)
    async def fsm_position(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        user = await get_target_user(context)

        try:
            position = validate_text_field(event.message.body.text, "Должность")
        except ValueError as error:
            await prompt_step(
                event,
                context,
                f"{error}\n\nВведите должность ещё раз:",
                user.position if user else None,
            )
            return

        await context.update_data(position=position)
        await go_macro_step(event, context)

    @dp.message_callback(AdminProfileFormStates.waiting_position, F.callback.payload == "prof:keep")
    async def keep_position(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        user = await get_target_user(context)

        if user is None or not user.position:
            await prompt_step(event, context, "Текущее значение не заполнено. Введите должность:", None)
            return

        await context.update_data(position=user.position)
        await go_macro_step(event, context)

    # === ШАГ 5. МАКРОРЕГИОН И ГОРОД ===

    @dp.message_callback(
        AdminProfileFormStates.waiting_macro_region,
        F.callback.payload.startswith("prof:macro:"),
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
                profile_admin_kb.get_macro_region_choice_kb(macro_regions),
            )
            return

        user = await get_target_user(context)
        city_name = await current_city_name(user)

        await context.update_data(macro_region_id=macro_id)
        await context.set_state(AdminProfileFormStates.waiting_city)

        await send_menu(
            event,
            context,
            with_current("Выберите город:", city_name),
            profile_admin_kb.get_city_choice_kb(cities),
        )

    @dp.message_callback(F.callback.payload == "prof:macro_back")
    async def cb_macro_back(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)
        await go_macro_step(event, context)

    @dp.message_callback(
        AdminProfileFormStates.waiting_city,
        F.callback.payload.startswith("prof:city:"),
    )
    async def fsm_city(event: MessageCallback, context: MemoryContext):
        city_id = int(event.callback.payload.split(":")[-1])

        await delete_callback_message(event)
        await context.update_data(city_id=city_id)
        await go_birth_step(event, context)

    # Кнопка «Оставить как есть» на шаге выбора макрорегиона или города:
    # сохраняем текущий город пользователя и идём дальше.
    @dp.message_callback(AdminProfileFormStates.waiting_macro_region, F.callback.payload == "prof:keep")
    @dp.message_callback(AdminProfileFormStates.waiting_city, F.callback.payload == "prof:keep")
    async def keep_city(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        user = await get_target_user(context)

        if user is None or user.city_id is None:
            await go_macro_step(event, context)
            return

        await context.update_data(city_id=user.city_id)
        await go_birth_step(event, context)

    # === ШАГ 6. ДАТА РОЖДЕНИЯ ===

    @dp.message_created(AdminProfileFormStates.waiting_birth_date, F.message.body.text)
    async def fsm_birth_date(event: MessageCreated, context: MemoryContext):
        await clear_last_bot_message(context)

        user = await get_target_user(context)
        birth = format_birth_date(user) if user else "не указана"
        birth_value = None if birth == "не указана" else birth

        try:
            birth_day, birth_month, birth_year = parse_birth_date(event.message.body.text)
        except ValueError as error:
            await prompt_step(
                event,
                context,
                f"{error}\n\nВведите дату рождения ещё раз:",
                birth_value,
            )
            return

        await save_profile(event, context, birth_day, birth_month, birth_year)

    @dp.message_callback(AdminProfileFormStates.waiting_birth_date, F.callback.payload == "prof:keep")
    async def keep_birth_date(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        user = await get_target_user(context)

        if user is None or user.birth_day is None:
            await prompt_step(
                event,
                context,
                "Текущая дата рождения не заполнена. Введите дату:",
                None,
            )
            return

        await save_profile(event, context, user.birth_day, user.birth_month, user.birth_year)
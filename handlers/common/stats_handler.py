import logging
from pathlib import Path

from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.types import Command, MessageCallback, MessageCreated

from keyboards.common import stats_kb
from repositories.report_repo import ReportRepo
from services.report_service import (
    build_annual_csv,
    build_text_report,
    format_month_label,
    format_short_name,
)
from states.common_states import StatsStates
from utils.charts import bar_chart, line_chart, pie_chart
from utils.ui_messages import (
    clear_last_bot_message,
    delete_callback_message,
    send_menu,
    send_menu_with_media,
)
from utils.validators import parse_date_to_iso


logger = logging.getLogger(__name__)

# Папка для годовых CSV-отчётов.
REPORTS_DIR = Path("data/reports")


def register_stats_handlers(
    dp: Dispatcher,
    bot,
    report_repo: ReportRepo,
    settings,
) -> None:
    """
    Статистика по тренингам: доступна всем ролям.
    """

    async def send_csv_report(event, context: MemoryContext, csv_path: Path, title: str) -> None:
        """Отправляет CSV-файл вместе с текстом и кнопками одним сообщением."""

        await send_menu_with_media(
            event,
            context,
            title,
            stats_kb.get_back_to_stats_menu_kb(),
            csv_path,
            bot,
        )

    async def send_report(
        event,
        context: MemoryContext,
        kind: str,
        period_key: str,
        start: str | None = None,
        end: str | None = None,
    ) -> None:
        """
        Генерирует текстовый отчёт и график, отправляет пользователю.
        """

        text = await build_text_report(
            report_repo,
            kind,
            period_key,
            settings.timezone,
            start,
            end,
        )

        if kind == "leads":
            rows = await report_repo.by_lead(start, end)
            items = [(format_short_name(r), r["cnt"]) for r in rows]
            chart_path = bar_chart(items, "Статистика по амбассадорам", f"chart_leads_{period_key}.png")
        elif kind == "cities":
            rows = await report_repo.by_city(start, end)
            items = [(r["name"], r["cnt"]) for r in rows]
            chart_path = bar_chart(items, "Статистика по городам", f"chart_cities_{period_key}.png")
        elif kind == "macro":
            rows = await report_repo.by_macro_region(start, end)
            items = [(r["name"], r["cnt"]) for r in rows]
            chart_path = bar_chart(items, "Статистика по макрорегионам", f"chart_macro_{period_key}.png")
        elif kind == "months":
            rows = await report_repo.by_month(start, end)
            items = [(format_month_label(r["month"]), r["cnt"]) for r in rows]
            chart_path = line_chart(items, "Динамика тренингов по месяцам", f"chart_months_{period_key}.png")
        elif kind == "formats":
            rows = await report_repo.by_format(start, end)
            items = [(r["name"], r["cnt"]) for r in rows]
            chart_path = pie_chart(items, "Статистика по форматам тренингов", f"chart_formats_{period_key}.png")
        else:
            await send_menu(
                event,
                context,
                "Неизвестный тип отчёта.",
                stats_kb.get_stats_menu_kb(),
            )
            return

        await send_menu_with_media(
            event,
            context,
            text,
            stats_kb.get_back_to_stats_menu_kb(),
            chart_path,
            bot,
        )

        await context.clear()

    # === МЕНЮ ===

    @dp.message_created(Command("stats"))
    async def cmd_stats(event: MessageCreated, context: MemoryContext):
        await context.clear()

        await send_menu(
            event,
            context,
            "Статистика по тренингам:",
            stats_kb.get_stats_menu_kb(),
        )

    @dp.message_callback(F.callback.payload == "stats:menu")
    async def cb_stats_menu(event: MessageCallback, context: MemoryContext):
        await context.clear()
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Статистика по тренингам:",
            stats_kb.get_stats_menu_kb(),
        )

    # === ВЫБОР СРЕЗА ===

    @dp.message_callback(F.callback.payload == "stats:leads")
    async def cb_stats_leads(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Статистика по амбассадорам.\n\nВыберите период:",
            stats_kb.get_period_choice_kb("leads"),
        )

    @dp.message_callback(F.callback.payload == "stats:cities")
    async def cb_stats_cities(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Статистика по городам.\n\nВыберите период:",
            stats_kb.get_period_choice_kb("cities"),
        )

    @dp.message_callback(F.callback.payload == "stats:macro")
    async def cb_stats_macro(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Статистика по макрорегионам.\n\nВыберите период:",
            stats_kb.get_period_choice_kb("macro"),
        )

    @dp.message_callback(F.callback.payload == "stats:months")
    async def cb_stats_months(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Динамика по месяцам.\n\nВыберите период:",
            stats_kb.get_period_choice_kb("months"),
        )

    @dp.message_callback(F.callback.payload == "stats:formats")
    async def cb_stats_formats(event: MessageCallback, context: MemoryContext):
        await delete_callback_message(event)

        await send_menu(
            event,
            context,
            "Статистика по форматам тренингов.\n\nВыберите период:",
            stats_kb.get_period_choice_kb("formats"),
        )

    @dp.message_callback(F.callback.payload == "stats:annual")
    async def cb_stats_annual(event: MessageCallback, context: MemoryContext):
        """Выбор года для годового отчёта."""

        await delete_callback_message(event)

        years = await report_repo.get_conducted_years()

        if not years:
            await send_menu(
                event,
                context,
                "Проведённых тренингов ещё нет.",
                stats_kb.get_stats_menu_kb(),
            )
            return

        await send_menu(
            event,
            context,
            "Годовой отчёт (CSV).\n\nВыберите год:",
            stats_kb.get_year_choice_kb(years),
        )

    # === ВЫБОР ПЕРИОДА ===

    @dp.message_callback(F.callback.payload.startswith("stats:period:"))
    async def cb_period_choice(event: MessageCallback, context: MemoryContext):
        """Обработка выбора периода и генерация отчёта."""

        await delete_callback_message(event)

        parts = event.callback.payload.split(":")
        kind = parts[2]
        period_key = parts[3]

        if period_key == "custom":
            await context.update_data(stats_kind=kind)
            await context.set_state(StatsStates.waiting_period_start)

            await send_menu(
                event,
                context,
                "Произвольный период.\n\nВведите дату начала в формате ДД.ММ.ГГГГ:",
                stats_kb.get_custom_period_kb(),
            )
            return

        await send_report(event, context, kind, period_key)

    @dp.message_created(StatsStates.waiting_period_start, F.message.body.text)
    async def fsm_period_start(event: MessageCreated, context: MemoryContext):
        """Получение даты начала произвольного периода."""

        await clear_last_bot_message(context)

        try:
            start_date = parse_date_to_iso(event.message.body.text)
        except ValueError as error:
            await send_menu(
                event,
                context,
                f"{error}\n\nВведите дату начала ещё раз:",
                stats_kb.get_custom_period_kb(),
            )
            return

        await context.update_data(period_start=start_date)
        await context.set_state(StatsStates.waiting_period_end)

        await send_menu(
            event,
            context,
            "Введите дату окончания в формате ДД.ММ.ГГГГ:",
            stats_kb.get_custom_period_kb(),
        )

    @dp.message_created(StatsStates.waiting_period_end, F.message.body.text)
    async def fsm_period_end(event: MessageCreated, context: MemoryContext):
        """Получение даты окончания произвольного периода."""

        await clear_last_bot_message(context)

        try:
            end_date = parse_date_to_iso(event.message.body.text)
        except ValueError as error:
            await send_menu(
                event,
                context,
                f"{error}\n\nВведите дату окончания ещё раз:",
                stats_kb.get_custom_period_kb(),
            )
            return

        data = await context.get_data()
        start_date = data.get("period_start")
        kind = data.get("stats_kind", "leads")

        if start_date > end_date:
            await send_menu(
                event,
                context,
                "Дата окончания должна быть позже даты начала.\n\nВведите дату окончания ещё раз:",
                stats_kb.get_custom_period_kb(),
            )
            return

        await send_report(
            event,
            context,
            kind,
            "custom",
            start=start_date,
            end=end_date,
        )

    # === ГОДОВОЙ ОТЧЁТ ===

    @dp.message_callback(F.callback.payload.startswith("stats:year:"))
    async def cb_year_choice(event: MessageCallback, context: MemoryContext):
        """Генерация годового отчёта в CSV."""

        await delete_callback_message(event)

        year = event.callback.payload.split(":")[-1]

        rows = await report_repo.annual_by_lead(year)

        if not rows:
            await send_menu(
                event,
                context,
                f"За {year} год нет проведённых тренингов.",
                stats_kb.get_stats_menu_kb(),
            )
            return

        csv_path = build_annual_csv(rows, year, REPORTS_DIR)

        await send_csv_report(event, context, csv_path, f"Годовой отчёт за {year} год готов.")
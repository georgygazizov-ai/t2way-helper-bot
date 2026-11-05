from maxapi.context import State, StatesGroup


class StatsStates(StatesGroup):
    """Состояния произвольного периода статистики."""

    waiting_period_start = State()
    waiting_period_end = State()
from maxapi.context import StatesGroup, State


class UserProfileEditStates(StatesGroup):
    """Состояния редактирования профиля пользователем."""
    waiting_position = State()
    waiting_macro_region = State()
    waiting_city = State()
    waiting_birth_date = State()
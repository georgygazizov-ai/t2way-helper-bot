from maxapi.context import StatesGroup, State


class MacroRegionStates(StatesGroup):
    """Состояния для работы с макрорегионами."""
    waiting_name = State()


class CityStates(StatesGroup):
    """Состояния для работы с городами."""
    waiting_macro_region = State()
    waiting_name = State()

class AdminProfileSearchStates(StatesGroup):
    """Состояния поиска пользователя администратором."""
    waiting_last_name = State()


class AdminProfileFormStates(StatesGroup):
    """Состояния заполнения карточки пользователя администратором."""
    waiting_last_name = State()
    waiting_first_name = State()
    waiting_patronymic = State()
    waiting_position = State()
    waiting_macro_region = State()
    waiting_city = State()
    waiting_birth_date = State()

class AdminRoleStates(StatesGroup):
    """Состояния поиска пользователя для смены роли."""
    waiting_last_name = State()
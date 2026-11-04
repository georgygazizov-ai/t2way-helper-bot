from dataclasses import dataclass


@dataclass
class MacroRegion:
    id: int
    name: str
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class City:
    id: int
    name: str
    macro_region_id: int
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class User:
    user_id: int
    last_name: str | None
    first_name: str | None
    patronymic: str | None
    position: str | None
    city_id: int | None
    birth_day: int | None
    birth_month: int | None
    birth_year: int | None
    role: str
    status: str
    is_profile_complete: bool
    registration_date: str
    created_at: str
    updated_at: str
    chat_id: int | None = None
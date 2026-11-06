-- Схема базы данных T2Way Helper Bot.
-- Все даты и временные метки храним в UTC.
-- Даты тренингов храним как TEXT в формате YYYY-MM-DD.

PRAGMA foreign_keys = ON;

-- =========================
-- 1. Макрорегионы
-- =========================

CREATE TABLE IF NOT EXISTS macro_regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2. Города
-- =========================

CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    macro_region_id INTEGER NOT NULL,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (macro_region_id)
        REFERENCES macro_regions(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =========================
-- 3. Пользователи
-- =========================

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER,

    last_name TEXT,
    first_name TEXT,
    patronymic TEXT,

    position TEXT,

    city_id INTEGER,

    birth_day INTEGER
        CHECK (
            birth_day IS NULL
            OR birth_day BETWEEN 1 AND 31
        ),

    birth_month INTEGER
        CHECK (
            birth_month IS NULL
            OR birth_month BETWEEN 1 AND 12
        ),

    birth_year INTEGER
        CHECK (
            birth_year IS NULL
            OR birth_year > 1900
        ),

    role TEXT NOT NULL
        CHECK (role IN ('trainer', 'admin', 'root')),

    status TEXT NOT NULL
        CHECK (status IN ('pending', 'active', 'left_chat')),

    is_profile_complete INTEGER NOT NULL DEFAULT 0
        CHECK (is_profile_complete IN (0, 1)),

    registration_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (city_id)
        REFERENCES cities(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    -- День и месяц рождения должны заполняться вместе.
    CHECK (
        (birth_day IS NULL AND birth_month IS NULL)
        OR
        (birth_day IS NOT NULL AND birth_month IS NOT NULL)
    ),

    -- Год можно указать только вместе с днём и месяцем.
    CHECK (
        birth_year IS NULL
        OR
        (birth_day IS NOT NULL AND birth_month IS NOT NULL)
    )
);

-- =========================
-- 4. Тренинги
-- =========================

CREATE TABLE IF NOT EXISTS trainings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    date TEXT NOT NULL,

    format TEXT NOT NULL
        CHECK (format IN ('Basic', 'Leadership')),

    city_id INTEGER NOT NULL,

    status TEXT NOT NULL
        CHECK (status IN ('assigned', 'conducted', 'cancelled')),

    created_by INTEGER NOT NULL,

    cancelled_by INTEGER,
    cancellation_reason TEXT,
    cancelled_at TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (city_id)
        REFERENCES cities(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (cancelled_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- =========================
-- 5. Ведущие тренингов
-- =========================

CREATE TABLE IF NOT EXISTS training_leads (
    training_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (training_id, user_id),

    FOREIGN KEY (training_id)
        REFERENCES trainings(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- =========================
-- 6. Напоминания
-- =========================

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    training_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    reminder_type TEXT NOT NULL
        CHECK (reminder_type IN ('assignment', 'week_before', 'day_before')),

    scheduled_for TEXT NOT NULL,

    is_sent INTEGER NOT NULL DEFAULT 0
        CHECK (is_sent IN (0, 1)),

    sent_at TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (training_id)
        REFERENCES trainings(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    -- Защита от случайного дубля одного и того же напоминания.
    UNIQUE (training_id, user_id, reminder_type, scheduled_for)
);

-- =========================
-- 7. Журнал ежедневных событий (защита от повторных отправок за один день)
-- =========================

CREATE TABLE IF NOT EXISTS daily_events_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_date TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    UNIQUE (event_type, event_date)
);

-- =========================
-- 8. Настройки приложения
-- =========================

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Индексы
-- =========================

CREATE INDEX IF NOT EXISTS idx_macro_regions_name
    ON macro_regions(name);

CREATE INDEX IF NOT EXISTS idx_macro_regions_active
    ON macro_regions(is_active);


CREATE INDEX IF NOT EXISTS idx_cities_name
    ON cities(name);

CREATE INDEX IF NOT EXISTS idx_cities_macro_region_id
    ON cities(macro_region_id);

CREATE INDEX IF NOT EXISTS idx_cities_active
    ON cities(is_active);


CREATE INDEX IF NOT EXISTS idx_users_status
    ON users(status);

CREATE INDEX IF NOT EXISTS idx_users_role
    ON users(role);

CREATE INDEX IF NOT EXISTS idx_users_city_id
    ON users(city_id);

CREATE INDEX IF NOT EXISTS idx_users_last_name
    ON users(last_name);

CREATE INDEX IF NOT EXISTS idx_users_birth
    ON users(birth_month, birth_day);


CREATE INDEX IF NOT EXISTS idx_trainings_date
    ON trainings(date);

CREATE INDEX IF NOT EXISTS idx_trainings_status
    ON trainings(status);

CREATE INDEX IF NOT EXISTS idx_trainings_city_id
    ON trainings(city_id);

CREATE INDEX IF NOT EXISTS idx_trainings_created_by
    ON trainings(created_by);


CREATE INDEX IF NOT EXISTS idx_training_leads_user_id
    ON training_leads(user_id);

CREATE INDEX IF NOT EXISTS idx_training_leads_training_id
    ON training_leads(training_id);


CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_for
    ON reminders(scheduled_for);

CREATE INDEX IF NOT EXISTS idx_reminders_sent
    ON reminders(is_sent, scheduled_for);

CREATE INDEX IF NOT EXISTS idx_reminders_training_id
    ON reminders(training_id);

CREATE INDEX IF NOT EXISTS idx_reminders_user_id
    ON reminders(user_id);
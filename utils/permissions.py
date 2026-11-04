# Роли пользователей в системе.
ROLE_TRAINER = "trainer"
ROLE_ADMIN = "admin"
ROLE_ROOT = "root"

# Административные роли: администратор и root.
ADMIN_ROLES = {ROLE_ADMIN, ROLE_ROOT}

# Человекочитаемые названия ролей для вывода в боте.
ROLE_TITLES = {
    ROLE_TRAINER: "Тренер",
    ROLE_ADMIN: "Администратор",
    ROLE_ROOT: "Root",
}


def role_title(role: str) -> str:
    """
    Возвращает название роли для отображения.
    """

    return ROLE_TITLES.get(role, role)


def is_admin(user) -> bool:
    """
    Возвращает True, если пользователь администратор или root.
    """

    return user.role in ADMIN_ROLES


def is_root(user) -> bool:
    """
    Возвращает True, если пользователь root.
    """

    return user.role == ROLE_ROOT
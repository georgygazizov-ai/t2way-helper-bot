import logging

from database.connection import Database
from database.models import User


logger = logging.getLogger(__name__)


class UserRepo:
    """
    Репозиторий для работы с пользователями.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def _row_to_model(self, row) -> User | None:
        """
        Преобразует строку из БД в модель User.
        """

        if row is None:
            return None

        return User(
            user_id=row["user_id"],
            last_name=row["last_name"],
            first_name=row["first_name"],
            patronymic=row["patronymic"],
            position=row["position"],
            city_id=row["city_id"],
            birth_day=row["birth_day"],
            birth_month=row["birth_month"],
            birth_year=row["birth_year"],
            role=row["role"],
            status=row["status"],
            is_profile_complete=bool(row["is_profile_complete"]),
            registration_date=row["registration_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            chat_id=row["chat_id"],
        )

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Ищет пользователя по его MAX ID.
        """

        query = "SELECT * FROM users WHERE user_id = ?"
        row = await self.db.fetchone(query, (user_id,))

        return self._row_to_model(row)

    async def get_admins(self) -> list[User]:
        """
        Возвращает всех активных администраторов и root.
        """

        query = """
            SELECT *
            FROM users
            WHERE role IN ('admin', 'root')
              AND status = 'active'
            ORDER BY user_id
        """

        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def create(
        self,
        user_id: int,
        role: str = "trainer",
        status: str = "active",
        first_name: str | None = None,
        last_name: str | None = None,
        chat_id: int | None = None,
    ) -> None:
        """
        Создаёт базовую запись пользователя.
        chat_id — это ID личного диалога с ботом в MAX.
        """

        query = """
            INSERT INTO users (user_id, role, status, first_name, last_name, chat_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        await self.db.execute(
            query,
            (user_id, role, status, first_name, last_name, chat_id),
        )

        logger.info(
            "[DB] Создан пользователь %s с ролью %s",
            user_id,
            role,
        )

    async def update_role(self, user_id: int, role: str) -> None:
        """
        Изменяет роль пользователя.
        """

        query = """
            UPDATE users
            SET role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """

        await self.db.execute(query, (role, user_id))

        logger.info(
            "[AUDIT] Пользователю %s назначена роль %s",
            user_id,
            role,
        )

    async def update_status(self, user_id: int, status: str) -> None:
        """
        Изменяет статус пользователя.
        """

        query = """
            UPDATE users
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """

        await self.db.execute(query, (status, user_id))

        logger.info(
            "[AUDIT] Пользователю %s назначен статус %s",
            user_id,
            status,
        )

    async def set_profile_complete(self, user_id: int) -> None:
        """
        Принудительно помечает профиль как заполненный.
        Используется, например, для root-пользователей.
        """

        query = """
            UPDATE users
            SET is_profile_complete = 1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """

        await self.db.execute(query, (user_id,))

    async def update_profile(
        self,
        user_id: int,
        last_name: str | None,
        first_name: str | None,
        patronymic: str | None,
        position: str | None,
        city_id: int | None,
        birth_day: int | None,
        birth_month: int | None,
        birth_year: int | None,
    ) -> None:
        """
        Обновляет профиль пользователя.

        Профиль считается заполненным, если указаны:
        - имя;
        - фамилия;
        - должность;
        - город.

        Дата рождения не является обязательной.
        """

        is_complete = 1 if (
            last_name
            and first_name
            and patronymic
            and position
            and city_id
            and birth_day
            and birth_month
        ) else 0

        query = """
            UPDATE users
            SET
                last_name = ?,
                first_name = ?,
                patronymic = ?,
                position = ?,
                city_id = ?,
                birth_day = ?,
                birth_month = ?,
                birth_year = ?,
                is_profile_complete = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """

        params = (
            last_name,
            first_name,
            patronymic,
            position,
            city_id,
            birth_day,
            birth_month,
            birth_year,
            is_complete,
            user_id,
        )

        await self.db.execute(query, params)

        logger.info(
            "[AUDIT] Обновлен профиль пользователя %s",
            user_id,
        )

    async def get_incomplete_profiles(self, include_root: bool = False) -> list[User]:
        """
        Возвращает активные пользователи с незаполненной карточкой.
        Root скрываем от обычных администраторов.
        """

        query = """
            SELECT *
            FROM users
            WHERE status = 'active'
              AND is_profile_complete = 0
        """

        if not include_root:
            query += " AND role != 'root'"

        query += " ORDER BY registration_date DESC"

        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def search_by_last_name(
        self,
        last_name_query: str,
        include_root: bool = False,
    ) -> list[User]:
        """
        Ищет активных пользователей по части фамилии.
        Для небольшого числа пользователей делаем фильтрацию в Python,
        чтобы корректно работать с кириллицей.
        """

        query = """
            SELECT *
            FROM users
            WHERE status = 'active'
              AND last_name IS NOT NULL
        """

        if not include_root:
            query += " AND role != 'root'"

        query += " ORDER BY last_name, first_name"

        rows = await self.db.fetchall(query)
        users = [self._row_to_model(row) for row in rows]

        search = last_name_query.lower().strip()

        return [
            user
            for user in users
            if search in (user.last_name or "").lower()
        ]

    async def update_chat_id(self, user_id: int, chat_id: int) -> None:
        """
        Обновляет ID личного диалога пользователя с ботом.
        """

        query = """
            UPDATE users
            SET chat_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """

        await self.db.execute(query, (chat_id, user_id))

    async def get_all_trainers(self) -> list[User]:
        """
        Возвращает всех активных тренеров и администраторов.
        Используется для выбора ведущих тренинга.
        """

        query = """
            SELECT *
            FROM users
            WHERE role IN ('trainer', 'admin')
              AND status = 'active'
            ORDER BY last_name, first_name
        """

        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def get_birthday_users(self, day: int, month: int) -> list[User]:
        """
        Возвращает активных пользователей, у которых сегодня день рождения.
        Root не поздравляем публично: он скрыт от остальных.
        """

        query = """
            SELECT *
            FROM users
            WHERE status = 'active'
              AND role != 'root'
              AND birth_day = ?
              AND birth_month = ?
            ORDER BY last_name, first_name
        """

        rows = await self.db.fetchall(query, (day, month))

        return [self._row_to_model(row) for row in rows]

    async def get_all_for_broadcast(self) -> list[User]:
        """Все активные пользователи с заполненным chat_id."""
        query = """
            SELECT * FROM users
            WHERE status = 'active' AND chat_id IS NOT NULL
            ORDER BY user_id
        """
        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def get_trainers_for_broadcast(self) -> list[User]:
        """Тренеры и администраторы, готовые к рассылке."""
        query = """
            SELECT * FROM users
            WHERE role IN ('trainer', 'admin')
              AND status = 'active'
              AND chat_id IS NOT NULL
            ORDER BY user_id
        """
        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def get_admins_for_broadcast(self) -> list[User]:
        """Администраторы и root, готовые к рассылке."""
        query = """
            SELECT * FROM users
            WHERE role IN ('admin', 'root')
              AND status = 'active'
              AND chat_id IS NOT NULL
            ORDER BY user_id
        """
        rows = await self.db.fetchall(query)
        return [self._row_to_model(row) for row in rows]

    async def get_by_city_for_broadcast(self, city_id: int) -> list[User]:
        """Пользователи конкретного города, готовые к рассылке."""
        query = """
            SELECT * FROM users
            WHERE city_id = ?
              AND status = 'active'
              AND chat_id IS NOT NULL
            ORDER BY user_id
        """
        rows = await self.db.fetchall(query, (city_id,))
        return [self._row_to_model(row) for row in rows]

    async def get_by_macro_region_for_broadcast(self, macro_region_id: int) -> list[User]:
        """Пользователи макрорегиона, готовые к рассылке."""
        query = """
            SELECT u.* FROM users u
            JOIN cities c ON u.city_id = c.id
            WHERE c.macro_region_id = ?
              AND u.status = 'active'
              AND u.chat_id IS NOT NULL
            ORDER BY u.user_id
        """
        rows = await self.db.fetchall(query, (macro_region_id,))
        return [self._row_to_model(row) for row in rows]
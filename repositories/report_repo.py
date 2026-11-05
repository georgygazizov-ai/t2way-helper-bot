import logging

from database.connection import Database


logger = logging.getLogger(__name__)


class ReportRepo:
    """
    Запросы статистики по проведённым тренингам.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    @staticmethod
    def _period_condition(start: str | None, end: str | None) -> tuple[str, tuple]:
        """
        Добавляет условие периода в запрос, если период задан.
        """

        if start and end:
            return " AND t.date BETWEEN ? AND ? ", (start, end)

        return "", ()

    async def total_conducted(self, start: str | None = None, end: str | None = None) -> int:
        """
        Общее количество проведённых тренингов за период.
        """

        cond, params = self._period_condition(start, end)

        query = f"""
            SELECT COUNT(*) AS cnt
            FROM trainings t
            WHERE t.status = 'conducted'{cond}
        """

        row = await self.db.fetchone(query, params)

        return int(row["cnt"]) if row else 0

    async def by_lead(self, start: str | None = None, end: str | None = None) -> list:
        """
        Статистика по амбассадорам: сколько проведённых тренингов у каждого.
        """

        cond, params = self._period_condition(start, end)

        query = f"""
            SELECT tl.user_id AS user_id,
                   u.last_name AS last_name,
                   u.first_name AS first_name,
                   u.patronymic AS patronymic,
                   COUNT(*) AS cnt
            FROM trainings t
            JOIN training_leads tl ON tl.training_id = t.id
            JOIN users u ON u.user_id = tl.user_id
            WHERE t.status = 'conducted'{cond}
            GROUP BY tl.user_id
            ORDER BY cnt DESC, u.last_name
        """

        return await self.db.fetchall(query, params)

    async def by_city(self, start: str | None = None, end: str | None = None) -> list:
        """
        Статистика по городам.
        """

        cond, params = self._period_condition(start, end)

        query = f"""
            SELECT c.name AS name, COUNT(*) AS cnt
            FROM trainings t
            JOIN cities c ON c.id = t.city_id
            WHERE t.status = 'conducted'{cond}
            GROUP BY c.name
            ORDER BY cnt DESC
        """

        return await self.db.fetchall(query, params)

    async def by_macro_region(self, start: str | None = None, end: str | None = None) -> list:
        """
        Статистика по макрорегионам.
        """

        cond, params = self._period_condition(start, end)

        query = f"""
            SELECT m.name AS name, COUNT(*) AS cnt
            FROM trainings t
            JOIN cities c ON c.id = t.city_id
            JOIN macro_regions m ON m.id = c.macro_region_id
            WHERE t.status = 'conducted'{cond}
            GROUP BY m.name
            ORDER BY cnt DESC
        """

        return await self.db.fetchall(query, params)

    async def by_month(self, start: str | None = None, end: str | None = None) -> list:
        """
        Статистика по месяцам.
        """

        cond, params = self._period_condition(start, end)

        query = f"""
            SELECT strftime('%Y-%m', t.date) AS month, COUNT(*) AS cnt
            FROM trainings t
            WHERE t.status = 'conducted'{cond}
            GROUP BY month
            ORDER BY month
        """

        return await self.db.fetchall(query, params)

    async def by_format(self, start: str | None = None, end: str | None = None) -> list:
        """
        Статистика по форматам тренингов.
        """

        cond, params = self._period_condition(start, end)

        query = f"""
            SELECT t.format AS name, COUNT(*) AS cnt
            FROM trainings t
            WHERE t.status = 'conducted'{cond}
            GROUP BY t.format
            ORDER BY cnt DESC
        """

        return await self.db.fetchall(query, params)

    async def get_conducted_years(self) -> list[str]:
        """
        Возвращает список годов, за которые есть проведённые тренинги.
        """

        query = """
            SELECT DISTINCT strftime('%Y', t.date) AS year
            FROM trainings t
            WHERE t.status = 'conducted'
            ORDER BY year DESC
        """

        rows = await self.db.fetchall(query)

        return [row["year"] for row in rows]

    async def annual_by_lead(self, year: str) -> list:
        """
        Годовой срез по амбассадорам с должностями.
        Сортировка по убыванию количества проведённых программ.
        """

        query = """
            SELECT tl.user_id AS user_id,
                   u.last_name AS last_name,
                   u.first_name AS first_name,
                   u.patronymic AS patronymic,
                   u.position AS position,
                   COUNT(*) AS cnt
            FROM trainings t
            JOIN training_leads tl ON tl.training_id = t.id
            JOIN users u ON u.user_id = tl.user_id
            WHERE t.status = 'conducted'
              AND strftime('%Y', t.date) = ?
            GROUP BY tl.user_id
            ORDER BY cnt DESC, u.last_name
        """

        return await self.db.fetchall(query, (year,))
from pathlib import Path
from typing import Any
import asyncio
import logging

import aiosqlite


logger = logging.getLogger(__name__)


class Database:
    """
    Простая обёртка над SQLite.

    Важно:
    - все запросы должны быть параметризованными;
    - прямой доступ к соединению снаружи лучше не использовать;
    - для будущих репозиториев будут методы execute/fetchone/fetchall.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def connection(self) -> aiosqlite.Connection:
        """
        Возвращает активное соединение.
        Если соединения нет, значит БД ещё не инициализирована.
        """

        if self._connection is None:
            raise RuntimeError("База данных не подключена")

        return self._connection

    async def connect(self) -> None:
        """
        Подключается к SQLite и включает нужные настройки.
        """

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Включаем внешние ключи.
        await self._connection.execute("PRAGMA foreign_keys = ON")

        # WAL-режим улучшает работу SQLite при параллельных чтении и записи.
        await self._connection.execute("PRAGMA journal_mode = WAL")

        # Если БД занята, ждём до 5 секунд, а не падаем сразу.
        await self._connection.execute("PRAGMA busy_timeout = 5000")

        await self._connection.commit()

        logger.info("[DB] База данных подключена: %s", self.db_path)

    async def close(self) -> None:
        """
        Закрывает соединение с БД.
        """

        if self._connection is not None:
            await self._connection.close()
            self._connection = None
            logger.info("[DB] Соединение с базой данных закрыто")

    async def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        """
        Выполняет запрос без возврата строк.
        Используется для INSERT, UPDATE, DELETE.
        """

        async with self._lock:
            await self.connection.execute(query, params)
            await self.connection.commit()

    async def fetchone(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> aiosqlite.Row | None:
        """
        Возвращает одну строку.
        """

        async with self._lock:
            cursor = await self.connection.execute(query, params)
            row = await cursor.fetchone()
            await cursor.close()
            return row

    async def fetchall(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> list[aiosqlite.Row]:
        """
        Возвращает список строк.
        """

        async with self._lock:
            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()
            return list(rows)

    async def execute_script(self, script: str) -> None:
        """
        Выполняет большой SQL-скрипт.
        Используется для создания таблиц и индексов.
        """

        async with self._lock:
            await self.connection.executescript(script)
            await self.connection.commit()
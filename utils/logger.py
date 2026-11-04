from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import logging
import sys


class MoscowFormatter(logging.Formatter):
    """
    Форматтер, который выводит время в нужном часовом поясе.
    Переопределяет стандартный formatTime, чтобы избежать проблем
    с глобальным logging.Formatter.converter.
    """

    def __init__(self, fmt=None, datefmt=None, tz_name="Europe/Moscow"):
        super().__init__(fmt, datefmt)
        self.tz = ZoneInfo(tz_name)

    def formatTime(self, record, datefmt=None):
        """
        Переводит время лога в нужный часовой пояс.
        """

        dt = datetime.fromtimestamp(record.created, self.tz)

        if datefmt:
            return dt.strftime(datefmt)

        return dt.strftime("%Y-%m-%d %H:%M:%S")


class DailyMoscowFileHandler(logging.Handler):
    """
    Пишет логи в файл по московской дате.

    Каждый новый день по Москве создаётся новый файл:
    logs/bot_2026-11-02.log
    """

    def __init__(self, log_dir: Path, timezone_name: str) -> None:
        super().__init__()

        self.log_dir = log_dir
        self.timezone_name = timezone_name
        self.current_date = None
        self.file = None

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._open_current_file()

    def _get_today(self):
        """
        Возвращает текущую дату в Москве.
        """

        return datetime.now(ZoneInfo(self.timezone_name)).date()

    def _build_file_path(self) -> Path:
        """
        Формирует путь к файлу лога на сегодня.
        """

        today = self._get_today()
        return self.log_dir / f"bot_{today.isoformat()}.log"

    def _open_current_file(self) -> None:
        """
        Открывает файл лога для текущей даты.
        """

        if self.file is not None:
            self.file.close()

        self.current_date = self._get_today()
        file_path = self._build_file_path()

        self.file = file_path.open("a", encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        """
        Записывает одну строку лога.
        Если дата изменилась, открывает новый файл.
        """
        try:
            today = self._get_today()

            if today != self.current_date:
                self._open_current_file()

            # Защита: если файл уже закрыт при остановке приложения, 
            # просто игнорируем запись, чтобы не падать.
            if self.file is None:
                return

            message = self.format(record)
            self.file.write(message + "\n")
            self.file.flush()

        except Exception:
            # При завершении программы могут возникать ошибки логирования 
            # от сторонних библиотек. Подавляем их, чтобы не пугать пользователя.
            pass

    def close(self) -> None:
        """
        Закрывает файл при остановке приложения.
        """

        if self.file is not None:
            self.file.close()
            self.file = None

        super().close()


def setup_logging(log_dir: Path, timezone_name: str) -> None:
    """
    Настраивает логирование:
    - в консоль;
    - в ежедневный файл.

    Префиксы событий будем добавлять в сообщениях:
    [SYSTEM], [DB], [SECURITY], [AUDIT], [ERROR].
    """

    formatter = MoscowFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        tz_name=timezone_name,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = DailyMoscowFileHandler(log_dir, timezone_name)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Очищаем старые обработчики, чтобы при повторном запуске не было дублей.
    root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
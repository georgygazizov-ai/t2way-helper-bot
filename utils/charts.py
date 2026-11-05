import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Рендер без окна (для сервера)
import matplotlib.pyplot as plt
from matplotlib import font_manager


logger = logging.getLogger(__name__)

# Фирменная палитра (6 цветов по ТЗ).
BRAND_COLORS = [
    "#ff3495",
    "#00bfff",
    "#a7fc00",
    "#0000ff",
    "#7700ff",
    "#ff4f12",
]

# Главный цвет для столбчатых диаграмм.
MAIN_COLOR = BRAND_COLORS[0]

# Папка для временных PNG-файлов графиков.
CHARTS_DIR = Path("data/charts")


def _ensure_charts_dir() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def _setup_russian_font() -> None:
    """
    Настраивает шрифт с поддержкой кириллицы.
    Пытается Arial → DejaVu Sans → Liberation Sans → Times New Roman.
    """

    preferred = ["Arial", "DejaVu Sans", "Liberation Sans", "Times New Roman"]

    available = {f.name for f in font_manager.fontManager.ttflist}

    for name in preferred:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            logger.info("[CHARTS] Выбран шрифт: %s", name)
            return

    plt.rcParams["axes.unicode_minus"] = False
    logger.warning("[CHARTS] Кириллический шрифт не найден, используется шрифт по умолчанию")


def _empty_chart(title: str, filename: str) -> Path:
    """
    Заглушка «Нет данных».
    """

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", fontsize=16)
    ax.set_title(title, fontsize=14, pad=10)
    ax.axis("off")

    path = CHARTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

    return path


def bar_chart(
    items: list[tuple[str, int]],
    title: str,
    filename: str,
) -> Path:
    """
    Столбчатая диаграмма одним главным цветом.
    Ось значений скрыта: цифры указаны подписями.
    """

    _ensure_charts_dir()
    _setup_russian_font()

    if not items:
        return _empty_chart(title, filename)

    names = [row[0] for row in items]
    values = [row[1] for row in items]

    # Для большого числа подписей разворачиваем график горизонтально.
    horizontal = len(items) > 8
    fig_width = 10 if horizontal else 9
    fig_height = max(4, 0.45 * len(items)) if horizontal else 6

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    if horizontal:
        ax.barh(names, values, color=MAIN_COLOR)
        ax.invert_yaxis()

        for i, value in enumerate(values):
            ax.text(value + 0.2, i, str(value), va="center", fontsize=10)

        # Скрываем ось значений (горизонтальную).
        ax.xaxis.set_visible(False)
        ax.spines[["top", "right", "bottom"]].set_visible(False)
    else:
        ax.bar(names, values, color=MAIN_COLOR)

        for i, value in enumerate(values):
            ax.text(i, value + 0.2, str(value), ha="center", fontsize=10)

        # Скрываем ось значений (вертикальную).
        ax.yaxis.set_visible(False)
        ax.spines[["top", "right", "left"]].set_visible(False)

    ax.set_title(title, fontsize=14, pad=12)

    path = CHARTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

    return path


def pie_chart(
    items: list[tuple[str, int]],
    title: str,
    filename: str,
) -> Path:
    """
    Круговая диаграмма (для среза по форматам тренингов).
    Цвета — первые из фирменной палитры.
    Подписи на секторах показывают количество, легенды нет.
    """

    _ensure_charts_dir()
    _setup_russian_font()

    if not items:
        return _empty_chart(title, filename)

    labels = [row[0] for row in items]
    values = [row[1] for row in items]
    colors = BRAND_COLORS[: len(items)]

    total = sum(values)

    def count_label(pct: float) -> str:
        """Показывает количество вместо процентов."""
        return str(int(round(pct * total / 100)))

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct=count_label,
        startangle=90,
        textprops={"fontsize": 12},
    )

    ax.set_title(title, fontsize=14, pad=12)

    path = CHARTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

    return path


def line_chart(
    items: list[tuple[str, int]],
    title: str,
    filename: str,
) -> Path:
    """
    Линейный график для временных рядов (помесячно).
    Ось значений скрыта: цифры указаны подписями.
    """

    _ensure_charts_dir()
    _setup_russian_font()

    if not items:
        return _empty_chart(title, filename)

    labels = [row[0] for row in items]
    values = [row[1] for row in items]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(labels, values, marker="o", color=MAIN_COLOR, linewidth=2, markersize=8)
    ax.fill_between(range(len(values)), values, alpha=0.15, color=MAIN_COLOR)

    for i, value in enumerate(values):
        ax.text(i, value + 0.2, str(value), ha="center", fontsize=10)

    # Скрываем ось значений (вертикальную).
    ax.yaxis.set_visible(False)
    ax.spines[["top", "right", "left"]].set_visible(False)

    ax.set_title(title, fontsize=14, pad=12)

    if len(labels) > 6:
        plt.xticks(rotation=45, ha="right")

    path = CHARTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

    return path
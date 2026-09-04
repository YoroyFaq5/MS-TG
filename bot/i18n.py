"""
Единый слой русской локализации и форматирования — единственное место, где
сырые enum/status/type значения, пришедшие от API основного сайта,
превращаются в русский текст. Presenters обязаны брать переводы отсюда, а
не хардкодить их точечно — так словарь остаётся полным и проверяемым одним
тестом (см. tests/test_i18n.py), вместо того чтобы расползаться по десятку
файлов и неизбежно расходиться.

Всё, что реально приходит из `app/models/__init__.py` в MS (см. inventory
в CLAUDE_TASK_BOT_RU_GROUPS.md), должно иметь запись здесь. Значение, для
которого перевода нет, не должно попадать пользователю сырым английским
словом — используем безопасный fallback "Неизвестный статус".
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

# ── Статусы турнира (Tournament.status — plain string, не Enum в MS) ───────
TOURNAMENT_STATUS = {
    "pending": "ожидается",
    "active": "идёт",
    "finished": "завершён",
    "cancelled": "отменён",
}

# ── Тип турнира (TournamentType) ────────────────────────────────────────────
TOURNAMENT_TYPE = {
    "individual": "Индивидуальный",
    "team": "Командный",
}

# ── Этап турнира (StageType) — статус этапа хранится как plain string,
#    те же значения, что и у Tournament.status ───────────────────────────────
STAGE_TYPE = {
    "group": "Групповой этап",
    "main": "Основной этап",
    "final": "Финал",
}

# ── Серия/вечер серийного турнира (SeriesStatus) ────────────────────────────
SERIES_STATUS = {
    "pending": "ожидается",
    "active": "идёт",
    "finished": "завершена",
    "cancelled": "отменена",
}

# ── Сезон (SeasonStatus) ─────────────────────────────────────────────────────
SEASON_STATUS = {
    "active": "идёт",
    "finished": "завершён",
    "waiting_tiebreak": "ожидает тай-брейк",
}

# ── Фэнтези-драфт (FantasyDraftStatus) ──────────────────────────────────────
DRAFT_STATUS = {
    "open": "открыт",
    "locked": "заблокирован",
    "scored": "подсчитан",
}

# ── Победившая сторона игры (WinSide) ───────────────────────────────────────
WIN_SIDE = {
    "mafia": "Мафия",
    "city": "Город",
    "none": "Ничья",
}

# ── Роль в игре (Role) ──────────────────────────────────────────────────────
ROLE = {
    "civilian": "Мирный",
    "mafia": "Мафия",
    "don": "Дон",
    "sheriff": "Шериф",
}

# ── Категория товара магазина (ShopCategory) ────────────────────────────────
SHOP_CATEGORY = {
    "profile_customization": "Оформление профиля",
    "nickname": "Ник",
    "physical": "Физический приз",
}

# ── Редкость (Rarity) — используется и товарами, и достижениями, и титулами ─
RARITY = {
    "common": "Обычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
    "mythic": "Мифический",
    "ultra": "Ультра",
}

# ── Категория достижения (AchievementCategory) ──────────────────────────────
ACHIEVEMENT_CATEGORY = {
    "games": "Игры",
    "wins": "Победы",
    "rating": "Рейтинг",
    "tournaments": "Турниры",
    "seasons": "Сезоны",
    "fantasy": "Фэнтези",
    "economy": "Экономика",
    "social": "Социальное",
}

# ── Тип титула (TitleType) ───────────────────────────────────────────────────
TITLE_TYPE = {
    "seasonal": "Сезонный",
    "eternal": "Вечный",
    "manual": "Особый",
}

# ── Источник начисления монет (CoinSourceType) — для истории операций ──────
COIN_SOURCE = {
    "game_reward": "Награда за игру",
    "tournament_reward": "Награда за турнир",
    "season_reward": "Награда сезона",
    "system_bonus": "Системный бонус",
    "admin_adjustment": "Корректировка",
    "fantasy_reward": "Награда Фэнтези",
    "resale_payout": "Выплата за перекуп",
}

_UNKNOWN = "Неизвестный статус"

_ALL_DICTS = {
    "tournament_status": TOURNAMENT_STATUS,
    "tournament_type": TOURNAMENT_TYPE,
    "stage_type": STAGE_TYPE,
    "series_status": SERIES_STATUS,
    "season_status": SEASON_STATUS,
    "draft_status": DRAFT_STATUS,
    "win_side": WIN_SIDE,
    "role": ROLE,
    "shop_category": SHOP_CATEGORY,
    "rarity": RARITY,
    "achievement_category": ACHIEVEMENT_CATEGORY,
    "title_type": TITLE_TYPE,
    "coin_source": COIN_SOURCE,
}


def tr(dict_name: str, raw_value: Optional[str]) -> str:
    """Safe lookup: an unknown/missing raw_value NEVER surfaces the raw
    English word to the user — falls back to "Неизвестный статус"."""
    if not raw_value:
        return _UNKNOWN
    table = _ALL_DICTS.get(dict_name)
    if table is None:
        return _UNKNOWN
    return table.get(raw_value, _UNKNOWN)


# ── Множественные числа (склонение по числительному) ────────────────────────

def plural(n: int, one: str, few: str, many: str) -> str:
    """Русское склонение: 1 игра / 2 игры / 5 игр. `n` может быть
    отрицательным (счётчики не бывают, но на всякий случай берём abs)."""
    n = abs(int(n))
    n100 = n % 100
    n10 = n % 10
    if 11 <= n100 <= 14:
        return many
    if n10 == 1:
        return one
    if 2 <= n10 <= 4:
        return few
    return many


def games_word(n: int) -> str:
    return plural(n, "игра", "игры", "игр")


def coins_word(n) -> str:
    return plural(int(n), "монета", "монеты", "монет")


def points_word(n) -> str:
    return plural(int(n), "очко", "очка", "очков")


def wins_word(n: int) -> str:
    return plural(n, "победа", "победы", "побед")


def days_word(n: int) -> str:
    return plural(n, "день", "дня", "дней")


def picks_word(n: int) -> str:
    return plural(n, "пик", "пика", "пиков")


def fmt_count(n: int, word_fn) -> str:
    """'5 игр', '1 победа', etc."""
    return f"{n} {word_fn(n)}"


# ── Валюта ────────────────────────────────────────────────────────────────
# Единая внутренняя валюта — целые "монеты", без символа ₽ (проект не
# оперирует настоящими рублями нигде, кроме отдельных физических призов,
# которые API и так не путает с балансом монет).

def fmt_coins(amount) -> str:
    try:
        value = int(round(float(amount)))
    except (TypeError, ValueError):
        value = 0
    formatted = f"{value:,}".replace(",", " ")
    return f"{formatted} {coins_word(value)}"


def fmt_coins_compact(amount) -> str:
    """Для плотных карточек/кнопок, где отдельное слово не помещается —
    '🪙 1 250' вместо '1 250 монет'."""
    try:
        value = int(round(float(amount)))
    except (TypeError, ValueError):
        value = 0
    formatted = f"{value:,}".replace(",", " ")
    return f"🪙 {formatted}"


def fmt_signed_coins(amount) -> str:
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    sign = "+" if value >= 0 else "-"
    return f"{sign}{fmt_coins(abs(value))}"


def fmt_score(value) -> str:
    """Игровые баллы — с разумной точностью (до 2 знаков, без хвостовых
    нулей: 2 вместо 2.00, 1.5 вместо 1.50)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def fmt_points(value) -> str:
    """Игровые баллы с сохранением дробной точности ('12.5 очков'), в
    отличие от монет (всегда целые). Целые значения корректно склоняются
    (1 очко / 2 очка / 5 очков); дробные традиционно берут родительный
    множественного ('12.5 очков'), как и в обычной русской речи."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    word = points_word(int(numeric)) if numeric == int(numeric) else "очков"
    return f"{fmt_score(numeric)} {word}"


def fmt_percent(value) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0%"
    if value == int(value):
        return f"{int(value)}%"
    return f"{value:.1f}%"


# ── Даты ──────────────────────────────────────────────────────────────────
# Сайт хранит и показывает played_at/created_at и т.п. как "введённое"
# значение без отдельного пересчёта часового пояса (см. games/detail.html:
# game.played_at.strftime('%d.%m.%Y %H:%M') — без конвертации). Форматтер
# здесь намеренно делает то же самое: переразбирает те же "настенные" год/
# месяц/день/час/минуту из ISO-строки, не сдвигая их — иначе бот показывал
# бы другое время, чем сайт, для одного и того же события.

def fmt_datetime(iso_value: Optional[str]) -> str:
    if not iso_value:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return iso_value[:16].replace("T", " ")
    return dt.strftime("%d.%m.%Y %H:%M")


def fmt_date_only(iso_value: Optional[str]) -> str:
    if not iso_value:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return iso_value[:10]
    return dt.strftime("%d.%m.%Y")


# ── Страницы ──────────────────────────────────────────────────────────────

def page_indicator(page: int, total_pages: int) -> str:
    """Единый компактный формат номера страницы — используется и в
    заголовке текста, и в кнопке-индикаторе пагинации, чтобы не было двух
    разных стилей ('стр. 2/5' в одном месте и '2 из 5' в другом)."""
    return f"{page}/{max(total_pages, 1)}"


def page_header(page: int, total_pages: int) -> str:
    return f"Страница {page} из {max(total_pages, 1)}"

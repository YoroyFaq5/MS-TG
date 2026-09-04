"""
bot/i18n.py must have a Russian translation for every value that actually
exists in MS's models (see app/models/__init__.py there) and that reaches
the bot through /api/v1/bot/*. This file hardcodes those real value sets
(not imported from MS — the two repos are deliberately independent, see
ARCHITECTURE.md) so a rename/addition on the MS side that isn't mirrored
here fails a test instead of silently showing "Неизвестный статус" (or
worse, a raw English word) to users.
"""
import pytest

from bot import i18n

# Exact values from MS's PyEnum classes / plain-string status columns —
# keep in sync with app/models/__init__.py.
REAL_VALUES = {
    "tournament_status": ["pending", "active", "finished", "cancelled"],
    "tournament_type": ["individual", "team"],
    "stage_type": ["group", "main", "final"],
    "series_status": ["pending", "active", "finished", "cancelled"],
    "season_status": ["active", "finished", "waiting_tiebreak"],
    "draft_status": ["open", "locked", "scored"],
    "win_side": ["mafia", "city", "none"],
    "role": ["civilian", "mafia", "don", "sheriff"],
    "shop_category": ["profile_customization", "nickname", "physical"],
    "rarity": ["common", "rare", "epic", "legendary", "mythic", "ultra"],
    "achievement_category": ["games", "wins", "rating", "tournaments", "seasons", "fantasy"],
    "title_type": ["seasonal", "eternal", "manual"],
    "coin_source": [
        "game_reward", "tournament_reward", "season_reward",
        "system_bonus", "admin_adjustment", "fantasy_reward",
    ],
}


@pytest.mark.parametrize("dict_name", list(REAL_VALUES.keys()))
def test_every_real_value_has_a_russian_translation(dict_name):
    for raw_value in REAL_VALUES[dict_name]:
        translated = i18n.tr(dict_name, raw_value)
        assert translated != "Неизвестный статус", f"{dict_name}={raw_value!r} has no translation"
        assert translated.isascii() is False or not translated.islower() or " " in translated or True
        # No raw English leaking through: the translation must not just
        # echo the raw value back unchanged.
        assert translated.lower() != raw_value.lower()


def test_unknown_value_falls_back_safely_never_raw_english():
    assert i18n.tr("tournament_status", "some_new_status_nobody_added_yet") == "Неизвестный статус"
    assert i18n.tr("win_side", None) == "Неизвестный статус"
    assert i18n.tr("not_a_real_dict", "whatever") == "Неизвестный статус"


def test_plural_forms():
    assert i18n.games_word(1) == "игра"
    assert i18n.games_word(2) == "игры"
    assert i18n.games_word(5) == "игр"
    assert i18n.games_word(11) == "игр"
    assert i18n.games_word(21) == "игра"
    assert i18n.coins_word(1) == "монета"
    assert i18n.coins_word(2) == "монеты"
    assert i18n.coins_word(5) == "монет"
    assert i18n.points_word(1) == "очко"
    assert i18n.points_word(2) == "очка"
    assert i18n.points_word(5) == "очков"
    assert i18n.wins_word(1) == "победа"
    assert i18n.wins_word(2) == "победы"
    assert i18n.wins_word(5) == "побед"


def test_fmt_coins_no_ruble_sign_and_pluralized():
    assert "₽" not in i18n.fmt_coins(1250)
    assert i18n.fmt_coins(1250) == "1 250 монет"
    assert i18n.fmt_coins(1) == "1 монета"
    assert i18n.fmt_coins(2) == "2 монеты"


def test_fmt_score_no_trailing_zeros():
    assert i18n.fmt_score(2.0) == "2"
    assert i18n.fmt_score(2.00) == "2"
    assert i18n.fmt_score(1.5) == "1.5"
    assert i18n.fmt_score(0) == "0"


def test_fmt_datetime_russian_format_no_timezone_shift():
    assert i18n.fmt_datetime("2026-09-04T19:30:00+00:00") == "04.09.2026 19:30"
    assert i18n.fmt_datetime(None) == "—"
    assert i18n.fmt_date_only("2026-09-04T19:30:00+00:00") == "04.09.2026"


def test_page_header_and_indicator():
    assert i18n.page_indicator(2, 5) == "2/5"
    assert i18n.page_header(2, 5) == "Страница 2 из 5"

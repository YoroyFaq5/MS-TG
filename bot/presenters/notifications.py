"""
Presenters for incoming events FROM the main site (not Telegram updates) —
pure functions without I/O, same as the rest of presenters/*.

Every builder returns (text, markup, category): `category` is one of
bot.storage.NOTIFICATION_CATEGORIES, used by bot/webhooks/events.py to
respect the recipient's notification preferences before sending anything.
`markup` gives each notification the contextual buttons the spec asks for
(open the game/tournament/fantasy screen this event is about, jump to
profile, or open notification settings) — every screen those buttons
target is implemented in the corresponding handlers/* module (menu,
tournaments, fantasy, gifts, notifications).
"""
from telebot import types

from bot import i18n
from bot.keyboards.nav import cb, home_button
from bot.ui import esc


def _settings_button() -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton("🔔 Настроить уведомления", callback_data=cb("notif", "settings"))


def _markup(*rows: list) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for row in rows:
        if row:
            markup.row(*row)
    markup.row(_settings_button(), home_button())
    return markup


def build_next_slot_message(player: dict):
    tournament = esc(player.get("tournament_name") or "турнире")
    round_number = player.get("round_number")
    table_number = player.get("table_number")
    seat_number = player.get("seat_number")
    text = (
        f"🎲 Новый раунд в «{tournament}»!\n"
        f"Раунд {round_number}, стол №{table_number}.\n"
        f"Твой слот — <b>{seat_number}</b>."
    )
    game_id = player.get("game_id")
    row = [types.InlineKeyboardButton("🎮 Открыть игру", callback_data=cb("game", "detail", game_id))] if game_id else []
    return text, _markup(row), "slot"


def build_achievement_granted_message(payload: dict):
    text = f"🎖 Новое достижение: <b>{esc(payload['achievement_name'])}</b>!"
    row = [types.InlineKeyboardButton("👤 Профиль", callback_data=cb("profile", "open"))]
    return text, _markup(row), "award"


def build_title_granted_message(payload: dict):
    text = f"🏅 Тебе выдан титул: <b>{esc(payload['title_name'])}</b>!"
    row = [
        types.InlineKeyboardButton("👤 Профиль", callback_data=cb("profile", "open")),
        types.InlineKeyboardButton("🏅 Мои титулы", callback_data=cb("ach", "titles")),
    ]
    return text, _markup(row), "award"


def build_item_bought_out_message(payload: dict):
    text = (
        f"💰 Твой предмет «{esc(payload['item_name'])}» перекупил {esc(payload['buyer_name'])} "
        f"за {i18n.fmt_coins(payload['offer_price'])} — тебе зачислено {i18n.fmt_coins(payload['payout'])}."
    )
    row = [types.InlineKeyboardButton("🎒 Инвентарь", callback_data=cb("inv", "list"))]
    return text, _markup(row), "shop"


def _fantasy_button(payload: dict) -> list:
    series_id = payload.get("tournament_series_id")
    tournament_id = payload.get("tournament_id")
    if series_id and tournament_id:
        return [types.InlineKeyboardButton(
            "🎯 Фэнтези", callback_data=cb("fantasy", "series", tournament_id, series_id),
        )]
    if tournament_id:
        return [types.InlineKeyboardButton("🎯 Фэнтези", callback_data=cb("fantasy", "tourn", tournament_id))]
    return []


def build_fantasy_result_message(payload: dict):
    text = f"🎯 Фэнтези: турнир «{esc(payload['tournament_name'])}» — {i18n.fmt_points(payload['points'])}."
    return text, _markup(_fantasy_button(payload)), "fantasy"


def build_fantasy_prize_message(payload: dict):
    text = (
        f"🎉 Фэнтези: {payload['place']} место в «{esc(payload['tournament_name'])}» — "
        f"+{i18n.fmt_coins(payload['amount'])}!"
    )
    return text, _markup(_fantasy_button(payload)), "fantasy"


def build_gift_received_message(payload: dict):
    text = f"🎁 {esc(payload['sender_name'])} подарил(а) тебе «{esc(payload['item_name'])}»!"
    if payload.get("message"):
        text += f"\n«{esc(payload['message'])}»"
    row = [types.InlineKeyboardButton("🎁 Мои подарки", callback_data=cb("gift", "inbox"))]
    return text, _markup(row), "gift"


def build_season_award_message(payload: dict):
    text = (
        f"🏆 Сезон «{esc(payload['season_name'])}»: место #{payload['rank']} — "
        f"+{i18n.fmt_coins(payload['amount'])}!"
    )
    season_id = payload.get("season_id")
    row = [types.InlineKeyboardButton("📈 Рейтинг сезона", callback_data=cb("season", "detail", season_id))] if season_id else []
    return text, _markup(row), "season"


def build_game_finished_message(payload: dict):
    icon = "✅" if payload["won"] else "❌"
    text = f"{icon} Игра завершена — {i18n.fmt_points(payload['total_score'])}."
    if payload.get("bonus_score"):
        bonus = payload["bonus_score"]
        sign = "+" if bonus >= 0 else ""
        text += f" (бонус {sign}{i18n.fmt_score(bonus)})"
    game_id = payload.get("game_id")
    row = [types.InlineKeyboardButton("🎮 Открыть игру", callback_data=cb("game", "detail", game_id))] if game_id else []
    return text, _markup(row), "game"

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

from bot.keyboards.nav import cb, home_button
from bot.ui import esc, fmt_money


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
    text = f"🏅 Вам выдан титул: <b>{esc(payload['title_name'])}</b>!"
    row = [
        types.InlineKeyboardButton("👤 Профиль", callback_data=cb("profile", "open")),
        types.InlineKeyboardButton("🏅 Мои титулы", callback_data=cb("ach", "titles")),
    ]
    return text, _markup(row), "award"


def build_item_bought_out_message(payload: dict):
    text = (
        f"💰 Ваш предмет «{esc(payload['item_name'])}» перекупил {esc(payload['buyer_name'])} "
        f"за {fmt_money(payload['offer_price'])} монет — вам зачислено {fmt_money(payload['payout'])}."
    )
    row = [types.InlineKeyboardButton("🎒 Инвентарь", callback_data=cb("inv", "list"))]
    return text, _markup(row), "shop"


def _fantasy_button(payload: dict) -> list:
    series_id = payload.get("tournament_series_id")
    tournament_id = payload.get("tournament_id")
    if series_id and tournament_id:
        return [types.InlineKeyboardButton(
            "🎯 Fantasy", callback_data=cb("fantasy", "series", tournament_id, series_id),
        )]
    if tournament_id:
        return [types.InlineKeyboardButton("🎯 Fantasy", callback_data=cb("fantasy", "tourn", tournament_id))]
    return []


def build_fantasy_result_message(payload: dict):
    text = f"🎯 Fantasy: турнир «{esc(payload['tournament_name'])}» — {payload['points']} очков."
    return text, _markup(_fantasy_button(payload)), "fantasy"


def build_fantasy_prize_message(payload: dict):
    text = (
        f"🎉 Fantasy: {payload['place']} место в «{esc(payload['tournament_name'])}» — "
        f"+{fmt_money(payload['amount'])} монет!"
    )
    return text, _markup(_fantasy_button(payload)), "fantasy"


def build_gift_received_message(payload: dict):
    text = f"🎁 {esc(payload['sender_name'])} подарил(а) вам «{esc(payload['item_name'])}»!"
    if payload.get("message"):
        text += f"\n«{esc(payload['message'])}»"
    row = [types.InlineKeyboardButton("🎁 Мои подарки", callback_data=cb("gift", "inbox"))]
    return text, _markup(row), "gift"


def build_season_award_message(payload: dict):
    text = (
        f"🏆 Сезон «{esc(payload['season_name'])}»: место #{payload['rank']} — "
        f"+{fmt_money(payload['amount'])} монет!"
    )
    season_id = payload.get("season_id")
    row = [types.InlineKeyboardButton("📈 Рейтинг сезона", callback_data=cb("season", "detail", season_id))] if season_id else []
    return text, _markup(row), "season"


def build_game_finished_message(payload: dict):
    icon = "✅" if payload["won"] else "❌"
    text = f"{icon} Игра завершена — {payload['total_score']} балл."
    if payload.get("bonus_score"):
        text += f" (бонус {payload['bonus_score']:+.1f})"
    game_id = payload.get("game_id")
    row = [types.InlineKeyboardButton("🎮 Открыть игру", callback_data=cb("game", "detail", game_id))] if game_id else []
    return text, _markup(row), "game"

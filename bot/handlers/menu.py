"""
Inline main menu dispatcher. `/start` (see start.py) sends the menu message
with the compact "🏠 Меню" Reply Keyboard attached; every subsequent menu
interaction is an inline keyboard editing that same message in place.

Each section's entry point below simply calls that domain's OWN already-
guarded callback handler with the SAME `call` object — no logic is
duplicated here, this file is purely a router from
"v1:nav:open:<section>" to the right module.
"""
import logging

from bot.telegram_bot import bot
from bot.presenters.menu import build_main_menu_message, build_reply_keyboard
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb, NOOP
from bot import storage

from bot.handlers import profile as profile_h
from bot.handlers import ratings as ratings_h
from bot.handlers import tournaments as tournaments_h
from bot.handlers import fantasy as fantasy_h
from bot.handlers import shop as shop_h
from bot.handlers import inventory as inventory_h
from bot.handlers import gifts as gifts_h
from bot.handlers import vs as vs_h
from bot.handlers import notif_settings as notif_h

logger = logging.getLogger(__name__)


@bot.callback_query_handler(func=lambda call: call.data == NOOP)
def handle_noop_callback(call) -> None:
    """The decorative page-indicator button in every pagination_row() (e.g.
    "3/5" in the middle of a Prev/Next row) — every OTHER callback handler
    is registered for a specific domain via `guarded_callback`'s own NOOP
    short-circuit, but that only fires for handlers that actually get
    invoked for THIS callback_data. Since no domain handler's `is_cb(...)`
    filter matches "v1:noop" itself, it needs its own top-level handler so
    Telegram's loading spinner doesn't spin forever waiting for an answer
    that would otherwise never come."""
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text == "🏠 Меню")
def menu_reply_button(message) -> None:
    storage.clear_fsm_state(message.chat.id)
    text, markup = build_main_menu_message()
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "nav", "home"))
@guarded_callback(bot, answer_immediately=True)
def handle_nav_home(call) -> None:
    storage.clear_fsm_state(call.message.chat.id)
    text, markup = build_main_menu_message()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "nav", "open"))
@guarded_callback(bot)
def handle_nav_open(call) -> None:
    # Deliberately NOT answer_immediately here: most branches below delegate
    # to another domain's OWN already-guarded handler (which answers for
    # itself, immediately, via its own decorator) — pre-answering here too
    # would just make every one of those a harmless-but-noisy double-answer.
    # Only the "tourn" branch calls a bare helper instead of a guarded
    # handler, so it answers for itself, first, right below.
    _, _, section = parse_cb(call.data)
    storage.clear_fsm_state(call.message.chat.id)

    if section == "profile":
        profile_h.handle_profile_open(call)
    elif section == "rating":
        ratings_h.handle_rating_hub_callback(call)
    elif section == "tourn":
        bot.answer_callback_query(call.id)
        tournaments_h.open_tournaments_list(call.message.chat.id, call.message.message_id)
    elif section == "fantasy":
        fantasy_h.handle_fantasy_events(call)
    elif section == "shop":
        shop_h.handle_shop_hub(call)
    elif section == "inv":
        inventory_h.handle_inventory_hub(call)
    elif section == "gift":
        gifts_h.handle_gift_hub(call)
    elif section == "vs":
        vs_h.handle_vs_hub_callback(call)
    elif section == "notif":
        notif_h.handle_notif_settings(call)
    else:
        bot.answer_callback_query(call.id)

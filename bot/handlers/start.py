"""
/start — the one required text command. Optionally carries a deep-link
payload (`/start g_123`, from a `t.me/<bot>?start=g_123` link on the main
site) that jumps straight to a specific screen instead of the plain main
menu — see bot/deeplink.py for the payload format and the site-side links
that produce these.
"""
import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.profile import resolve
from bot.presenters.profile import build_not_linked_message, build_welcome_back_message
from bot.presenters.menu import build_main_menu_message, build_reply_keyboard
from bot.presenters.group import build_group_start_message
from bot.deeplink import resolve_deep_link
from bot.chat_policy import is_group
from bot.ui import error_state

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["start"])
def handle_start(message) -> None:
    if is_group(message.chat.type):
        # Group /start never resolves or shows a linked-account status —
        # that's personal data (CLAUDE_TASK_BOT_RU_GROUPS.md, п.2.4) — and
        # ignores any deep-link payload, since every deep-link target is a
        # private-chat screen anyway.
        text, markup = build_group_start_message()
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return

    telegram_id = message.from_user.id
    try:
        data = resolve(api_client, telegram_id)
    except ApiError:
        logger.exception("resolve() failed for /start")
        bot.send_message(message.chat.id, error_state("Не удалось связаться с сайтом."))
        return

    if data.get("linked"):
        text, _ = build_welcome_back_message(data["display_name"])
    else:
        text, _ = build_not_linked_message()
    bot.send_message(message.chat.id, text, reply_markup=build_reply_keyboard())

    parts = (message.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    screen = resolve_deep_link(payload, telegram_id) if payload else None
    if screen:
        screen_text, screen_markup = screen
        bot.send_message(message.chat.id, screen_text, reply_markup=screen_markup)
    else:
        menu_text, menu_markup = build_main_menu_message()
        bot.send_message(message.chat.id, menu_text, reply_markup=menu_markup)

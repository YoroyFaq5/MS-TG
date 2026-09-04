import logging

from bot.telegram_bot import bot
from bot.presenters.notif_settings import build_notification_settings_message
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot import storage

logger = logging.getLogger(__name__)


def _edit(call, text, markup):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "notif", "settings"))
@guarded_callback(bot)
def handle_notif_settings(call) -> None:
    prefs = storage.get_notification_prefs(call.from_user.id)
    _edit(call, *build_notification_settings_message(prefs))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "notif", "toggle"))
@guarded_callback(bot)
def handle_notif_toggle(call) -> None:
    _, _, category = parse_cb(call.data)
    telegram_id = call.from_user.id
    prefs = storage.get_notification_prefs(telegram_id)
    new_value = not prefs.get(category, True)
    storage.set_notification_pref(telegram_id, category, new_value)
    prefs = storage.get_notification_prefs(telegram_id)
    _edit(call, *build_notification_settings_message(prefs))

import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.profile import get_profile, get_stats, resolve
from bot.api_client.endpoints.economy import get_balance, get_economy_history
from bot.api_client.endpoints.achievements import get_achievements
from bot.presenters.profile import build_not_linked_message, build_profile_card
from bot.presenters.hub import build_profile_hub_message
from bot.presenters.stats import build_stats_message
from bot.presenters.economy import build_balance_message
from bot.presenters.achievements import build_achievements_message
from bot.presenters.account import build_account_status_message
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb
from bot.ui import error_state

logger = logging.getLogger(__name__)


def _edit(call, text, markup):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.message_handler(commands=["me"])
def handle_me(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = get_profile(api_client, telegram_id)
    except ApiError:
        logger.exception("/me failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить профиль."))
        return

    text, markup = build_profile_hub_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["stats"])
def handle_stats(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = get_stats(api_client, telegram_id)
    except ApiError:
        logger.exception("/stats failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить статистику."))
        return

    text, markup = build_stats_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "profile", "open"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_profile_open(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    data = get_profile(api_client, telegram_id)
    _edit(call, *build_profile_hub_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "profile", "stats"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_profile_stats(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    data = get_stats(api_client, telegram_id)
    _edit(call, *build_stats_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "profile", "achievements"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_profile_achievements(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    items = get_achievements(api_client, telegram_id)
    _edit(call, *build_achievements_message(items))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "profile", "balance"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_profile_balance(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    balance_data = get_balance(api_client, telegram_id)
    history_items = get_economy_history(api_client, telegram_id, limit=5)
    _edit(call, *build_balance_message(balance_data["balance"], history_items))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "profile", "account"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_profile_account(call) -> None:
    telegram_id = call.from_user.id
    data = resolve(api_client, telegram_id)
    if not data.get("linked"):
        _edit(call, *build_not_linked_message())
        return
    _edit(call, *build_account_status_message(data["display_name"]))

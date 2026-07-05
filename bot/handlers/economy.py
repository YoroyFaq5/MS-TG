import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.economy import get_balance, get_economy_history
from bot.presenters.profile import build_not_linked_message
from bot.presenters.economy import build_balance_message
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["balance"])
def handle_balance(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        balance_data = get_balance(api_client, telegram_id)
        history_items = get_economy_history(api_client, telegram_id, limit=5)
    except ApiError:
        logger.exception("/balance failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить баланс, попробуйте позже.")
        return

    text, markup = build_balance_message(balance_data["balance"], history_items)
    bot.send_message(message.chat.id, text, reply_markup=markup)

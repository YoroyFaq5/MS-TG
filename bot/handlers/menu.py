import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.profile import resolve
from bot.presenters.profile import build_not_linked_message
from bot.presenters.account import build_account_status_message

from bot.handlers.profile import handle_me, handle_stats
from bot.handlers.ratings import handle_rating
from bot.handlers.history import handle_history
from bot.handlers.economy import handle_balance
from bot.handlers.achievements import handle_achievements
from bot.handlers.tournaments import handle_tournaments
from bot.handlers.vs import handle_vs_menu

logger = logging.getLogger(__name__)

_FANTASY_HELP_TEXT = (
    "🎯 <b>Fantasy</b>\n\n"
    "Узнайте ID турнира в разделе 🎮 Турниры, затем:\n"
    "/fantasy &lt;id&gt; — мой драфт\n"
    "/fantasy_available &lt;id&gt; — доступные игроки (выбор/снятие — кнопками)\n"
    "/fantasy_create &lt;id&gt; — создать драфт\n"
    "/fantasy_leaderboard &lt;id&gt; — таблица лидеров"
)


@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def menu_profile(message) -> None:
    handle_me(message)


@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def menu_stats(message) -> None:
    handle_stats(message)


@bot.message_handler(func=lambda m: m.text == "🏆 Рейтинг")
def menu_rating(message) -> None:
    handle_rating(message)


@bot.message_handler(func=lambda m: m.text == "📜 История")
def menu_history(message) -> None:
    handle_history(message)


@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def menu_balance(message) -> None:
    handle_balance(message)


@bot.message_handler(func=lambda m: m.text == "🏅 Достижения")
def menu_achievements(message) -> None:
    handle_achievements(message)


@bot.message_handler(func=lambda m: m.text == "🎮 Турниры")
def menu_tournaments(message) -> None:
    handle_tournaments(message)


@bot.message_handler(func=lambda m: m.text == "🎯 Fantasy")
def menu_fantasy(message) -> None:
    bot.send_message(message.chat.id, _FANTASY_HELP_TEXT)


@bot.message_handler(func=lambda m: m.text == "🆚 Кто круче")
def menu_vs(message) -> None:
    handle_vs_menu(message)


@bot.message_handler(func=lambda m: m.text == "⚙️ Аккаунт")
def menu_account(message) -> None:
    telegram_id = message.from_user.id
    try:
        data = resolve(api_client, telegram_id)
    except ApiError:
        logger.exception("menu account resolve failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось проверить привязку, попробуйте позже.")
        return

    if data.get("linked"):
        text, markup = build_account_status_message(data["display_name"])
    else:
        text, markup = build_not_linked_message()
    bot.send_message(message.chat.id, text, reply_markup=markup)

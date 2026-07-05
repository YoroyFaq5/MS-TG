import logging
from typing import Optional

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.fantasy import (
    get_my_draft, create_draft, add_pick, remove_pick, get_leaderboard, get_available,
)
from bot.presenters.profile import build_not_linked_message
from bot.presenters.fantasy import (
    build_my_draft_message, build_no_draft_message, build_available_message,
    build_leaderboard_message,
)
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


def _parse_int_arg(message, min_args: int = 1) -> Optional[list]:
    parts = (message.text or "").split()
    args = parts[1:]
    if len(args) < min_args or not all(a.isdigit() for a in args[:min_args]):
        return None
    return [int(a) for a in args[:min_args]]


@bot.message_handler(commands=["fantasy"])
def handle_fantasy(message) -> None:
    args = _parse_int_arg(message)
    if not args:
        bot.send_message(message.chat.id, "Использование: <code>/fantasy &lt;id турнира&gt;</code>")
        return
    tournament_id = args[0]
    telegram_id = message.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        draft = get_my_draft(api_client, telegram_id, tournament_id)
    except ApiNotFound:
        text, markup = build_no_draft_message(tournament_id)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    except ApiError:
        logger.exception("/fantasy failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить драфт, попробуйте позже.")
        return

    text, markup = build_my_draft_message(draft)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["fantasy_create"])
def handle_fantasy_create(message) -> None:
    args = _parse_int_arg(message)
    if not args:
        bot.send_message(message.chat.id, "Использование: <code>/fantasy_create &lt;id турнира&gt;</code>")
        return
    tournament_id = args[0]
    telegram_id = message.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        create_draft(api_client, telegram_id, tournament_id)
    except ApiError as e:
        bot.send_message(message.chat.id, f"⚠️ {e}")
        return

    bot.send_message(
        message.chat.id,
        f"Драфт создан ✅ Доступные игроки: <code>/fantasy_available {tournament_id}</code>",
    )


@bot.message_handler(commands=["fantasy_available"])
def handle_fantasy_available(message) -> None:
    args = _parse_int_arg(message)
    if not args:
        bot.send_message(message.chat.id, "Использование: <code>/fantasy_available &lt;id турнира&gt;</code>")
        return
    tournament_id = args[0]
    telegram_id = message.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        players = get_available(api_client, telegram_id, tournament_id)
    except ApiError as e:
        bot.send_message(message.chat.id, f"⚠️ {e}")
        return

    text, markup = build_available_message(players, tournament_id)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["fantasy_pick"])
def handle_fantasy_pick(message) -> None:
    args = _parse_int_arg(message, min_args=2)
    if not args:
        bot.send_message(
            message.chat.id,
            "Использование: <code>/fantasy_pick &lt;id турнира&gt; &lt;id игрока&gt;</code>",
        )
        return
    tournament_id, player_id = args
    telegram_id = message.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        draft = get_my_draft(api_client, telegram_id, tournament_id)
        add_pick(api_client, telegram_id, draft["id"], player_id)
    except ApiNotFound:
        text, markup = build_no_draft_message(tournament_id)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    except ApiError as e:
        bot.send_message(message.chat.id, f"⚠️ {e}")
        return

    bot.send_message(message.chat.id, "Игрок добавлен в драфт ✅")


@bot.message_handler(commands=["fantasy_unpick"])
def handle_fantasy_unpick(message) -> None:
    args = _parse_int_arg(message, min_args=2)
    if not args:
        bot.send_message(
            message.chat.id,
            "Использование: <code>/fantasy_unpick &lt;id турнира&gt; &lt;id игрока&gt;</code>",
        )
        return
    tournament_id, player_id = args
    telegram_id = message.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        draft = get_my_draft(api_client, telegram_id, tournament_id)
        remove_pick(api_client, telegram_id, draft["id"], player_id)
    except ApiNotFound:
        text, markup = build_no_draft_message(tournament_id)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    except ApiError as e:
        bot.send_message(message.chat.id, f"⚠️ {e}")
        return

    bot.send_message(message.chat.id, "Игрок убран из драфта ✅")


@bot.message_handler(commands=["fantasy_leaderboard"])
def handle_fantasy_leaderboard(message) -> None:
    args = _parse_int_arg(message)
    if not args:
        bot.send_message(message.chat.id, "Использование: <code>/fantasy_leaderboard &lt;id турнира&gt;</code>")
        return
    tournament_id = args[0]

    try:
        entries = get_leaderboard(api_client, tournament_id)
    except ApiError:
        logger.exception("/fantasy_leaderboard failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить лидерборд, попробуйте позже.")
        return

    text, markup = build_leaderboard_message(entries, tournament_id)
    bot.send_message(message.chat.id, text, reply_markup=markup)

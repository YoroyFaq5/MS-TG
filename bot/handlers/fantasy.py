import logging

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


@bot.callback_query_handler(func=lambda call: call.data.startswith("fantasy_my:"))
def handle_fantasy_my_callback(call) -> None:
    tournament_id = int(call.data.split(":", 1)[1])
    telegram_id = call.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
        else:
            try:
                draft = get_my_draft(api_client, telegram_id, tournament_id)
                text, markup = build_my_draft_message(draft)
            except ApiNotFound:
                text, markup = build_no_draft_message(tournament_id)
    except ApiError:
        logger.exception("fantasy_my callback failed")
        bot.answer_callback_query(call.id, "⚠️ Не удалось получить драфт, попробуйте позже.")
        return

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("fantasy_create:"))
def handle_fantasy_create_callback(call) -> None:
    tournament_id = int(call.data.split(":", 1)[1])
    telegram_id = call.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id)
            return
        create_draft(api_client, telegram_id, tournament_id)
        players = get_available(api_client, telegram_id, tournament_id)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}")
        return

    text, markup = build_available_message(players, tournament_id)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Драфт создан ✅")


@bot.callback_query_handler(func=lambda call: call.data.startswith("fantasy_avail:"))
def handle_fantasy_avail_callback(call) -> None:
    tournament_id = int(call.data.split(":", 1)[1])
    telegram_id = call.from_user.id

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
        else:
            players = get_available(api_client, telegram_id, tournament_id)
            text, markup = build_available_message(players, tournament_id)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}")
        return

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith(("fpick:", "funpick:")))
def handle_fantasy_pick_callback(call) -> None:
    action, tid, pid = call.data.split(":")
    tournament_id, player_id = int(tid), int(pid)
    telegram_id = call.from_user.id

    try:
        draft = get_my_draft(api_client, telegram_id, tournament_id)
        if action == "fpick":
            add_pick(api_client, telegram_id, draft["id"], player_id)
            players = get_available(api_client, telegram_id, tournament_id)
            text, markup = build_available_message(players, tournament_id)
        else:
            remove_pick(api_client, telegram_id, draft["id"], player_id)
            draft = get_my_draft(api_client, telegram_id, tournament_id)
            text, markup = build_my_draft_message(draft)
    except ApiNotFound:
        text, markup = build_no_draft_message(tournament_id)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}")
        return

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Готово ✅")


@bot.callback_query_handler(func=lambda call: call.data.startswith("fantasy_lb:"))
def handle_fantasy_lb_callback(call) -> None:
    tournament_id = int(call.data.split(":", 1)[1])

    try:
        entries = get_leaderboard(api_client, tournament_id)
    except ApiError:
        logger.exception("fantasy_lb callback failed")
        bot.answer_callback_query(call.id, "⚠️ Не удалось получить лидерборд, попробуйте позже.")
        return

    text, markup = build_leaderboard_message(entries, tournament_id)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

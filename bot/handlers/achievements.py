import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.achievements import (
    get_achievements, pin, unpin, get_titles, equip_title, unequip_title,
)
from bot.presenters.profile import build_not_linked_message
from bot.presenters.achievements import build_achievements_message, build_titles_message
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["achievements"])
def handle_achievements(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        items = get_achievements(api_client, telegram_id)
    except ApiError:
        logger.exception("/achievements failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить достижения, попробуйте позже.")
        return

    text, markup = build_achievements_message(items)
    bot.send_message(message.chat.id, text, reply_markup=markup)


def _toggle_pin(action: str, achievement_id: int, telegram_id: int):
    action_fn = pin if action == "pin" else unpin
    action_fn(api_client, telegram_id, achievement_id)
    items = get_achievements(api_client, telegram_id)
    return build_achievements_message(items)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "ach", "pin") or is_cb(call.data, "ach", "unpin"))
@guarded_callback(bot, sensitive=True, private_only=True)
def handle_achievement_toggle_callback(call) -> None:
    """Новые сообщения используют versioned `v1:ach:pin:<id>` (см.
    build_achievements_message) — CLAUDE_TASK_BOT_RU_GROUPS.md п.5.3.
    Обратная совместимость со старыми кнопками без версии (`ach:pin:<id>`,
    уже отправленными до этого перехода) не требует отдельного обработчика:
    parse_cb()/is_cb() и так лениво терпят отсутствие префикса `v1:` —
    старый формат распознаётся тем же самым фильтром и тем же кодом ниже."""
    _, action, achievement_id = parse_cb(call.data)
    achievement_id = int(achievement_id)
    telegram_id = call.from_user.id
    try:
        text, markup = _toggle_pin(action, achievement_id, telegram_id)
    except ApiError:
        logger.exception("achievement pin/unpin toggle failed")
        bot.answer_callback_query(call.id, "⚠️ Не удалось выполнить действие, попробуйте позже.")
        return
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Готово ✅")


@bot.message_handler(commands=["titles"])
def handle_titles(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        items = get_titles(api_client, telegram_id)
    except ApiError:
        logger.exception("/titles failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить титулы, попробуйте позже.")
        return

    text, markup = build_titles_message(items)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "ach", "titles"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_titles_callback(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        text, markup = build_not_linked_message()
    else:
        items = get_titles(api_client, telegram_id)
        text, markup = build_titles_message(items)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "title", "equip"))
@guarded_callback(bot, sensitive=True, private_only=True)
def handle_title_equip_callback(call) -> None:
    _, _, player_title_id = parse_cb(call.data)
    telegram_id = call.from_user.id
    try:
        equip_title(api_client, telegram_id, int(player_title_id))
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    items = get_titles(api_client, telegram_id)
    text, markup = build_titles_message(items)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Экипирован ✅")


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "title", "unequip"))
@guarded_callback(bot, sensitive=True, private_only=True)
def handle_title_unequip_callback(call) -> None:
    telegram_id = call.from_user.id
    try:
        unequip_title(api_client, telegram_id)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    items = get_titles(api_client, telegram_id)
    text, markup = build_titles_message(items)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Снят")

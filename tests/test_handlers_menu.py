from unittest.mock import MagicMock, patch

from bot.keyboards.nav import cb


def _fake_message(chat_id=555, text="", from_id=111, chat_type="private"):
    m = MagicMock()
    m.chat.id = chat_id
    m.chat.type = chat_type
    m.from_user.id = from_id
    m.text = text
    return m


def _fake_call(data, chat_id=555, message_id=999, from_id=111, call_id="cbid1"):
    call = MagicMock()
    call.data = data
    call.id = call_id
    call.from_user.id = from_id
    call.message.chat.id = chat_id
    call.message.chat.type = "private"
    call.message.message_id = message_id
    return call


def test_noop_callback_is_always_answered():
    """The decorative pagination page-indicator button must never leave a
    stuck Telegram loading spinner."""
    from bot.handlers.menu import handle_noop_callback
    from bot.keyboards.nav import NOOP

    call = _fake_call(NOOP)
    with patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_noop_callback(call)
    mock_answer.assert_called_once_with("cbid1")


def test_menu_reply_button_sends_inline_main_menu():
    from bot.handlers.menu import menu_reply_button

    message = _fake_message(text="🏠 Меню")
    with patch("bot.telegram_bot.bot.send_message") as mock_send, \
         patch("bot.storage.clear_fsm_state") as mock_clear:
        menu_reply_button(message)
    mock_clear.assert_called_once_with(555, 111)
    assert "Главное меню" in mock_send.call_args[0][1]


def test_menu_reply_button_rejected_in_group():
    from bot.handlers.menu import menu_reply_button

    message = _fake_message(text="🏠 Меню", chat_type="group")
    with patch("bot.telegram_bot.bot.send_message") as mock_send, \
         patch("bot.storage.clear_fsm_state") as mock_clear:
        menu_reply_button(message)

    mock_clear.assert_not_called()
    assert "личном чате" in mock_send.call_args[0][1]


def test_handle_nav_home_edits_message_and_answers():
    from bot.handlers.menu import handle_nav_home

    call = _fake_call(cb("nav", "home"))
    with patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer, \
         patch("bot.storage.clear_fsm_state"):
        handle_nav_home(call)
    assert "Главное меню" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once_with("cbid1")


def test_handle_nav_open_dispatches_to_each_section():
    from bot.handlers.menu import handle_nav_open

    dispatch_targets = {
        "profile": "bot.handlers.profile.handle_profile_open",
        "rating": "bot.handlers.ratings.handle_rating_hub_callback",
        "fantasy": "bot.handlers.fantasy.handle_fantasy_events",
        "shop": "bot.handlers.shop.handle_shop_hub",
        "inv": "bot.handlers.inventory.handle_inventory_hub",
        "gift": "bot.handlers.gifts.handle_gift_hub",
        "vs": "bot.handlers.vs.handle_vs_hub_callback",
        "notif": "bot.handlers.notif_settings.handle_notif_settings",
    }
    for section, target in dispatch_targets.items():
        call = _fake_call(cb("nav", "open", section))
        with patch(target) as mock_handler, patch("bot.storage.clear_fsm_state"):
            handle_nav_open(call)
        mock_handler.assert_called_once_with(call)


def test_handle_nav_open_tourn_calls_shared_list_helper():
    from bot.handlers.menu import handle_nav_open

    call = _fake_call(cb("nav", "open", "tourn"))
    with patch("bot.handlers.tournaments.open_tournaments_list") as mock_open, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer, \
         patch("bot.storage.clear_fsm_state"):
        handle_nav_open(call)
    mock_open.assert_called_once_with(555, 999)
    mock_answer.assert_called_once_with("cbid1")


def test_handle_nav_open_unknown_section_just_answers():
    from bot.handlers.menu import handle_nav_open

    call = _fake_call(cb("nav", "open", "nonexistent"))
    with patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer, \
         patch("bot.storage.clear_fsm_state"):
        handle_nav_open(call)
    mock_answer.assert_called_once_with("cbid1")

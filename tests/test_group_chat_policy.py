"""
Group-vs-private access policy (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 2):
personal and mutating callbacks must reject a group-chat tap outright —
never reaching the underlying site API — and keep working normally in a
private chat. See bot/dispatch.py::guarded_callback(private_only=...) and
bot/chat_policy.py.
"""
from unittest.mock import MagicMock, patch

from bot.keyboards.nav import cb


def _fake_callback(data, telegram_id=111, chat_id=-100555, message_id=999, call_id=42, chat_type="group"):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.chat.type = chat_type
    c.message.message_id = message_id
    c.id = call_id
    return c


def test_mutating_shop_buy_rejected_in_group_never_calls_api():
    from bot.handlers.shop import handle_shop_buy

    call = _fake_callback(cb("shop", "buy", 1, "-"), chat_type="group")
    with patch("bot.handlers.shop.buy_item") as mock_buy, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_shop_buy(call)

    mock_buy.assert_not_called()
    mock_answer.assert_called_once()
    assert mock_answer.call_args.kwargs.get("show_alert") is True


def test_mutating_shop_buy_works_normally_in_private():
    from bot.handlers.shop import handle_shop_buy

    call = _fake_callback(cb("shop", "buy", 1, "-"), chat_type="private")
    item = {"id": 1, "name": "Frame", "price": 100.0}
    with patch("bot.handlers.shop.buy_item") as mock_buy, \
         patch("bot.handlers.shop.get_item_detail", return_value=item), \
         patch("bot.telegram_bot.bot.edit_message_text"), \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_shop_buy(call)

    mock_buy.assert_called_once()


def test_personal_balance_rejected_in_supergroup_never_calls_api():
    from bot.handlers.profile import handle_profile_balance

    call = _fake_callback(cb("profile", "balance"), chat_type="supergroup")
    with patch("bot.handlers.profile.get_balance") as mock_balance, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_profile_balance(call)

    mock_balance.assert_not_called()
    mock_answer.assert_called_once()


def test_personal_balance_works_normally_in_private():
    from bot.handlers.profile import handle_profile_balance

    call = _fake_callback(cb("profile", "balance"), chat_type="private")
    with patch("bot.handlers.profile.resolve_player_id", return_value=7), \
         patch("bot.handlers.profile.get_balance", return_value={"balance": 10.0}) as mock_balance, \
         patch("bot.handlers.profile.get_economy_history", return_value=[]), \
         patch("bot.telegram_bot.bot.edit_message_text"), \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_profile_balance(call)

    mock_balance.assert_called_once()


def test_main_menu_navigation_rejected_in_group():
    """The whole rich inline menu (CLAUDE_TASK_BOT_RU_GROUPS.md п.7.5) is
    private-only, even for a plain navigation tap, not just mutating ones —
    a forwarded main-menu message must not turn into a live menu in a
    group."""
    from bot.handlers.menu import handle_nav_open

    call = _fake_callback(cb("nav", "open", "shop"), chat_type="group")
    with patch("bot.handlers.shop.handle_shop_hub") as mock_shop_hub, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_nav_open(call)

    mock_shop_hub.assert_not_called()
    mock_answer.assert_called_once()


def test_fsm_starting_callback_rejected_in_group():
    """Any FSM-with-free-text scenario entry point must be private-only
    (CLAUDE_TASK_BOT_RU_GROUPS.md п.2.1: "любые FSM-сценарии со свободным
    вводом")."""
    from bot.handlers.gifts import handle_gift_send_start

    call = _fake_callback(cb("gift", "send"), chat_type="group")
    with patch("bot.handlers.gifts.get_giftable_items") as mock_items, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_gift_send_start(call)

    mock_items.assert_not_called()
    mock_answer.assert_called_once()

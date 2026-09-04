"""
bot/dispatch.py::guarded_callback — the shared callback_query wrapper every
new-domain handler uses: swallows the shared NOOP button, enforces the
double-tap lock for sensitive actions, and guarantees exactly one
answer_callback_query on any path the wrapped handler didn't reach itself.
"""
from unittest.mock import MagicMock, patch

from bot.dispatch import guarded_callback
from bot.keyboards.nav import NOOP
from bot.api_client.exceptions import ApiError


def _fake_call(data="v1:x:y", call_id="cbid", from_id=111):
    call = MagicMock()
    call.data = data
    call.id = call_id
    call.from_user.id = from_id
    return call


def test_noop_is_answered_and_never_reaches_handler():
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot)(handler)

    call = _fake_call(data=NOOP)
    wrapped(call)

    handler.assert_not_called()
    bot.answer_callback_query.assert_called_once_with("cbid")


def test_successful_handler_is_not_double_answered():
    bot = MagicMock()

    def handler(call):
        bot.answer_callback_query(call.id, "done")

    wrapped = guarded_callback(bot)(handler)
    wrapped(_fake_call())

    bot.answer_callback_query.assert_called_once_with("cbid", "done")


def test_unhandled_exception_gets_exactly_one_answer():
    bot = MagicMock()

    def handler(call):
        raise RuntimeError("boom")

    wrapped = guarded_callback(bot)(handler)
    wrapped(_fake_call())  # must not raise

    bot.answer_callback_query.assert_called_once()


def test_api_error_gets_exactly_one_answer():
    bot = MagicMock()

    def handler(call):
        raise ApiError("business failure")

    wrapped = guarded_callback(bot)(handler)
    wrapped(_fake_call())

    bot.answer_callback_query.assert_called_once()


def test_sensitive_double_tap_is_rejected_without_running_handler_twice():
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot, sensitive=True)(handler)

    call_1 = _fake_call(data="v1:shop:buy:1", call_id="a")
    call_2 = _fake_call(data="v1:shop:buy:1", call_id="b")  # same actor + same action

    wrapped(call_1)
    wrapped(call_2)

    assert handler.call_count == 1
    # The (mock) handler itself never self-answers on its own success path
    # (real handlers do) — the one answer_callback_query call observed here
    # is the rejection toast for the blocked second tap.
    bot.answer_callback_query.assert_called_once_with("b", "⏳ Уже обрабатывается — подождите секунду.", show_alert=False)


def test_sensitive_lock_is_per_actor_and_action():
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot, sensitive=True)(handler)

    wrapped(_fake_call(data="v1:shop:buy:1", from_id=111))
    wrapped(_fake_call(data="v1:shop:buy:2", from_id=111))  # different item
    wrapped(_fake_call(data="v1:shop:buy:1", from_id=222))  # different user

    assert handler.call_count == 3


def test_answer_immediately_answers_before_calling_handler():
    bot = MagicMock()
    call_order = []
    bot.answer_callback_query.side_effect = lambda *a, **k: call_order.append("answer")
    handler = MagicMock(side_effect=lambda call: call_order.append("handler"))

    wrapped = guarded_callback(bot, answer_immediately=True)(handler)
    wrapped(_fake_call())

    assert call_order == ["answer", "handler"]
    bot.answer_callback_query.assert_called_once_with("cbid")
    handler.assert_called_once()


def test_answer_immediately_failure_sends_message_instead_of_second_answer():
    """Once answered up front, a failure can't re-answer the same
    callback_query — the fallback must be a plain sent message, not a
    second (guaranteed-to-fail) answer_callback_query call."""
    bot = MagicMock()

    def handler(call):
        raise RuntimeError("boom")

    wrapped = guarded_callback(bot, answer_immediately=True)(handler)
    wrapped(_fake_call())  # must not raise

    bot.answer_callback_query.assert_called_once_with("cbid")  # only the immediate one
    bot.send_message.assert_called_once()


def test_private_only_rejects_group_callback_without_running_handler():
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot, private_only=True)(handler)

    call = _fake_call()
    call.message.chat.type = "group"
    wrapped(call)

    handler.assert_not_called()
    bot.answer_callback_query.assert_called_once()
    args, kwargs = bot.answer_callback_query.call_args
    assert args[0] == "cbid"
    assert kwargs.get("show_alert") is True


def test_private_only_allows_private_chat_callback():
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot, private_only=True, answer_immediately=True)(handler)

    call = _fake_call()
    call.message.chat.type = "private"
    wrapped(call)

    handler.assert_called_once()


def test_private_only_does_not_touch_sensitive_lock_when_rejected():
    """A group tap on a private_only+sensitive callback must not acquire
    (or later appear to be blocking) the double-tap lock — it's rejected
    before the lock logic runs at all."""
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot, sensitive=True, private_only=True)(handler)

    group_call = _fake_call(data="v1:shop:buy:1")
    group_call.message.chat.type = "group"
    wrapped(group_call)
    handler.assert_not_called()

    # The same actor/action from a private chat right after must still work
    # normally — proves no lock was left behind by the rejected group tap.
    private_call = _fake_call(data="v1:shop:buy:1")
    private_call.message.chat.type = "private"
    wrapped(private_call)
    handler.assert_called_once()


def test_answer_immediately_skipped_for_noop_and_locked_paths():
    bot = MagicMock()
    handler = MagicMock()
    wrapped = guarded_callback(bot, sensitive=True, answer_immediately=True)(handler)

    call_1 = _fake_call(data="v1:shop:buy:1", call_id="a")
    call_2 = _fake_call(data="v1:shop:buy:1", call_id="b")
    wrapped(call_1)
    wrapped(call_2)  # blocked by the double-tap lock — must not ALSO get the immediate answer

    assert handler.call_count == 1
    # One immediate answer for call_1, one lock-rejection toast for call_2 — never both for call_2.
    assert bot.answer_callback_query.call_count == 2

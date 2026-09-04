"""
Shared callback_query dispatch wrapper.

Every existing handler already ends its own success path with exactly one
`bot.answer_callback_query(...)` call — this wrapper must never add a
second one on that path (Telegram's answerCallbackQuery is meant to be
called once per callback). What it DOES guarantee, uniformly, for every
handler that opts in:

- the shared no-op button (`v1:noop`, used for decorative pagination
  labels) is answered and swallowed before reaching any real handler;
- a double-tap on a `sensitive=True` action (purchase, gift, draft
  creation, ...) is rejected with a friendly toast instead of running
  twice, using a short-lived lock in bot/storage.py;
- ANY exception the handler raises without having answered the callback
  itself (typed API errors it forgot to catch, a bug, a network blip) still
  results in exactly one answer_callback_query — never a stuck Telegram
  loading spinner, and never an unhandled 500 bubbling out of the webhook.

Handlers keep answering their own success/expected-failure paths exactly
as before; this only fills the gap for paths that never got that far.
"""
from __future__ import annotations

import functools
import logging

from bot import storage
from bot.api_client.exceptions import ApiError
from bot.keyboards.nav import NOOP

logger = logging.getLogger(__name__)

_DEFAULT_ERROR_TOAST = "⚠️ Не удалось выполнить действие, попробуйте позже."
_LOCKED_TOAST = "⏳ Уже обрабатывается — подождите секунду."


def guarded_callback(bot, *, sensitive: bool = False, lock_ttl: float = 8.0, answer_immediately: bool = False):
    """Decorator factory for `@bot.callback_query_handler` targets.

    Usage:
        @bot.callback_query_handler(func=lambda c: is_cb(c.data, "shop", "buy"))
        @guarded_callback(bot, sensitive=True)
        def handle_shop_buy(call): ...

    answer_immediately: answer the callback_query right away (clearing
    Telegram's loading spinner) BEFORE calling the handler, instead of
    leaving it to the handler's own trailing answer_callback_query() call.
    Telegram's callback_query token has a short validity window that is
    SEPARATE from the overall webhook response deadline — any outbound
    network call (to this site's API, to fetch data) before answering
    risks the token already being expired by the time the handler gets
    around to it, which fails as "query is too old" and — since that
    failure itself gets swallowed to avoid crashing the webhook — leaves
    the button looking dead with literally no feedback to the user (see
    the incident that motivated this: bot/handlers/vs.py, Сравнить
    игроков, timing out on a slow host).

    Use answer_immediately=True for simple navigation/display callbacks
    that don't need the answer's own text/alert to convey anything (the
    vast majority — a plain "clear the spinner" is all they ever did).
    Once answer_immediately=True, the wrapped handler must NOT call
    bot.answer_callback_query itself. Leave it False (default) for
    sensitive=True / mutating handlers whose answer text depends on the
    outcome of the action (e.g. "Готово ✅" vs a specific error) — those
    must keep answering with their own result at the end; on failure this
    decorator falls back to a plain sent message instead of a toast, since
    the callback can no longer be answered a second time.
    """

    def decorator(handler):
        @functools.wraps(handler)
        def wrapped(call):
            if call.data == NOOP:
                bot.answer_callback_query(call.id)
                return

            lock_key = None
            if sensitive:
                lock_key = f"cb:{call.from_user.id}:{call.data}"
                if not storage.try_acquire_action_lock(lock_key, lock_ttl):
                    bot.answer_callback_query(call.id, _LOCKED_TOAST, show_alert=False)
                    return

            if answer_immediately:
                try:
                    bot.answer_callback_query(call.id)
                except Exception:
                    logger.exception("Failed to answer callback %s immediately", handler.__name__)

            # Deliberately NOT released here on success: the lock is meant
            # to survive for its full TTL so a second tap that arrives
            # shortly AFTER the first request already finished (the common
            # real-world "didn't see it register, tapped again" case, not
            # just two requests overlapping mid-flight) is still rejected.
            # It is released early only on failure, so a rejected/errored
            # attempt doesn't block a legitimate retry for the rest of the
            # TTL window.
            try:
                handler(call)
            except ApiError:
                logger.exception("API error in callback handler %s", handler.__name__)
                if lock_key:
                    storage.release_action_lock(lock_key)
                _report_failure(bot, call, answer_immediately)
            except Exception:
                logger.exception("Unhandled error in callback handler %s", handler.__name__)
                if lock_key:
                    storage.release_action_lock(lock_key)
                _report_failure(bot, call, answer_immediately)

        return wrapped

    return decorator


def _report_failure(bot, call, already_answered: bool) -> None:
    """Surface a handler failure to the user — a toast via
    answer_callback_query() normally, or (if the callback was already
    answered up front by answer_immediately=True, so a second answer
    would itself fail) a plain sent message instead."""
    try:
        if already_answered:
            bot.send_message(call.message.chat.id, _DEFAULT_ERROR_TOAST)
        else:
            bot.answer_callback_query(call.id, _DEFAULT_ERROR_TOAST)
    except Exception:
        pass

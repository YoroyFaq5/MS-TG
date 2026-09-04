"""
Navigation building blocks — the small shared "design system" for every
inline screen in the bot: a versioned callback_data encoder, common
Home/Back buttons, and a pagination row. Centralizing this means every
screen agrees on the same callback_data shape and the same 64-byte safety
margin instead of each handler module inventing its own ad hoc scheme.

Callback data shape: "v1:<domain>:<action>[:<arg>...]" — the "v1:" prefix
means a future incompatible change to a domain's argument shape can bump to
"v2:" and both can be routed side by side during rollout instead of every
in-flight message's buttons suddenly decoding into garbage. Only short,
already-public identifiers belong in here (numeric IDs, page numbers, short
enum values) — never prices, balances, permissions or anything else a user
could tamper with to their own benefit; every mutating handler re-resolves
and re-validates from the site regardless of what a callback_data claims.
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

from telebot import types

logger = logging.getLogger(__name__)

CALLBACK_MAX_BYTES = 64

# A no-op target for purely decorative buttons (e.g. a "page 2/5" label in
# the middle of a pagination row) — answered immediately, changes nothing.
NOOP = "v1:noop"


class CallbackDataTooLong(ValueError):
    """Raised by cb() when the encoded string would exceed Telegram's
    64-byte callback_data limit (CLAUDE_TASK_BOT_RU_GROUPS.md, п.5.4) —
    Telegram itself would silently refuse to attach such a button, which
    used to surface as a mysteriously dead button days later. Raising here
    instead means: a test or a dev run catches the bug immediately at its
    source, and in production the surrounding guarded_callback()/handler
    error handling turns it into one friendly "не удалось выполнить
    действие" message instead of a keyboard with a button that does
    nothing when tapped."""


def cb(*parts: object) -> str:
    """Build a versioned callback_data string: cb("shop", "item", 42) ->
    "v1:shop:item:42"."""
    data = "v1:" + ":".join(str(p) for p in parts)
    if len(data.encode("utf-8")) > CALLBACK_MAX_BYTES:
        logger.error("callback_data exceeds %d bytes: %r", CALLBACK_MAX_BYTES, data)
        raise CallbackDataTooLong(data)
    return data


def parse_cb(data: str) -> list[str]:
    """"v1:shop:item:42" -> ["shop", "item", "42"] (version prefix stripped)."""
    parts = data.split(":")
    return parts[1:] if parts and parts[0] == "v1" else parts


def is_cb(data: str, domain: str, action: Optional[str] = None) -> bool:
    parts = parse_cb(data)
    if not parts or parts[0] != domain:
        return False
    if action is not None and (len(parts) < 2 or parts[1] != action):
        return False
    return True


def home_button() -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton("🏠 Главное меню", callback_data=cb("nav", "home"))


def back_button(target: str, label: str = "← Назад") -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton(label, callback_data=target)


def nav_row(back_target: Optional[str] = None, include_home: bool = True) -> list[types.InlineKeyboardButton]:
    """Standard footer row for every nested screen — a specific "back to
    parent" target (each screen knows its own logical parent) plus the
    always-available "home" shortcut. Omit back_target on top-level section
    screens (their only sensible parent already IS home)."""
    row = []
    if back_target:
        row.append(back_button(back_target))
    if include_home:
        row.append(home_button())
    return row


def add_nav_footer(
    markup: Optional[types.InlineKeyboardMarkup], back_target: Optional[str] = None, include_home: bool = True,
) -> types.InlineKeyboardMarkup:
    """Appends the standard Back/Home footer row to an existing markup —
    accepts None (a presenter with no buttons of its own) and creates a
    fresh markup in that case, so every screen ends up with SOME way back
    even if its own content has no buttons."""
    if markup is None:
        markup = types.InlineKeyboardMarkup()
    row = nav_row(back_target, include_home)
    if row:
        markup.row(*row)
    return markup


def pagination_row(
    prefix: str, page: int, total_pages: int, extra_parts: Iterable[object] = (),
) -> list[types.InlineKeyboardButton]:
    """prefix is a full callback_data prefix such as "v1:shop:list" — the
    page number (and any extra_parts, e.g. a category filter) are appended
    after it. Always includes a non-interactive page indicator in the
    middle so the row's meaning is clear even with only one page."""
    extra = ":" + ":".join(str(p) for p in extra_parts) if extra_parts else ""
    total_pages = max(total_pages, 1)
    row = []
    if page > 1:
        row.append(types.InlineKeyboardButton("◀️", callback_data=f"{prefix}:{page - 1}{extra}"))
    row.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data=NOOP))
    if page < total_pages:
        row.append(types.InlineKeyboardButton("▶️", callback_data=f"{prefix}:{page + 1}{extra}"))
    return row


def confirm_row(confirm_cb: str, cancel_cb: str, confirm_label: str = "✅ Подтвердить", cancel_label: str = "✖️ Отмена") -> list[types.InlineKeyboardButton]:
    return [
        types.InlineKeyboardButton(confirm_label, callback_data=confirm_cb),
        types.InlineKeyboardButton(cancel_label, callback_data=cancel_cb),
    ]

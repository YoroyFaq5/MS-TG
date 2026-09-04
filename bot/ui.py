"""
UI helpers shared by every presenter — the small "design system" the bot
was missing: safe HTML escaping, common formatting, and empty/error state
text. Zero I/O, zero Telegram/telebot imports beyond `types` for typing —
same "pure function" contract as the rest of presenters/*.

Why this exists: every presenter interpolates data that ultimately comes
from the site (display names, item/tournament/title names, gift notes,
bios) straight into an HTML parse_mode string. A display name containing
`<`, `>` or `&` breaks Telegram's HTML entity parser — at best the message
silently fails to send (Telegram's sendMessage returns 400 "can't parse
entities"), at worst it lets a crafted name inject a stray tag into a
message. `esc()` is the one place that risk is closed; every presenter
must route untrusted strings through it before interpolating.
"""
from __future__ import annotations

from html import escape as _html_escape
from typing import Optional


def esc(value) -> str:
    """HTML-escape any value for safe interpolation into an HTML parse_mode
    message. None/falsy becomes an empty string (never the literal "None")."""
    if value is None:
        return ""
    return _html_escape(str(value), quote=False)


def truncate(text: str, limit: int = 120) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def fmt_money(amount) -> str:
    try:
        return f"{float(amount):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def fmt_signed(amount) -> str:
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "0"
    sign = "+" if amount >= 0 else ""
    return f"{sign}{amount:.1f}"


def fmt_date(iso_value: Optional[str]) -> str:
    if not iso_value:
        return "—"
    return iso_value[:10]


def empty_state(text: str = "Здесь пока пусто.") -> str:
    return f"🗒 {esc(text)}"


def error_state(text: str = "Не удалось выполнить запрос, попробуйте позже.") -> str:
    return f"⚠️ {esc(text)}"


def stale_state(text: str = "Это действие уже неактуально — обновите экран.") -> str:
    return f"♻️ {esc(text)}"


def title_line(icon: str, text: str) -> str:
    return f"{icon} <b>{esc(text)}</b>"


def stat_row(label: str, value) -> str:
    return f"{esc(label)}: <b>{esc(value)}</b>"

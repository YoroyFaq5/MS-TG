"""
The bot's own @username — needed to build "Открыть бота" deep-link URL
buttons (t.me/<username>?start=<payload>) for group screens that need to
send the user into a private chat (CLAUDE_TASK_BOT_RU_GROUPS.md, п.2.1).

TELEGRAM_BOT_USERNAME is OPTIONAL (unlike the rest of bot/config.py's
required vars): if unset, we fetch it once via bot.get_me() and cache it
for the process lifetime, so existing deployments don't need a new
required env var to keep working — but setting it explicitly in
production avoids that one extra Telegram API round trip at first use.
"""
from __future__ import annotations

_cached_username: str | None = None


def get_bot_username() -> str:
    global _cached_username
    if _cached_username:
        return _cached_username

    from bot.config import Config
    if Config.TELEGRAM_BOT_USERNAME:
        _cached_username = Config.TELEGRAM_BOT_USERNAME
        return _cached_username

    from bot.telegram_bot import bot
    _cached_username = bot.get_me().username
    return _cached_username


def bot_url() -> str:
    """Plain 'open the bot' link — no payload, just lands on /start."""
    return f"https://t.me/{get_bot_username()}"


def deep_link_url(payload: str) -> str:
    return f"https://t.me/{get_bot_username()}?start={payload}"

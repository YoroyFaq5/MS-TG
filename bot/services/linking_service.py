"""
Бот-специфичное правило: "не привязан — предложи привязать" — общее для
всех команд, которым нужен конкретный игрок. Сам резолв (какой telegram_id
соответствует какому player_id) выполняет MS через /api/v1/bot/resolve —
здесь только склейка вызова с этим правилом, никакой отдельной логики.
"""
from typing import Optional

from bot.api_client.endpoints.profile import resolve


def resolve_player_id(api_client, telegram_id: int) -> Optional[int]:
    data = resolve(api_client, telegram_id)
    return data.get("player_id") if data.get("linked") else None

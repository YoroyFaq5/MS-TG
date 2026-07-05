"""
Обёртки над /api/v1/bot/{resolve,profile,stats,compare} основного сайта.
Каждая функция принимает уже созданный ApiClient (см. bot/telegram_bot.py)
— сами по себе это просто типизированные HTTP-вызовы, без бизнес-логики.
"""
from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def resolve(client: ApiClient, telegram_id: int) -> dict:
    return client.get(f"{_PREFIX}/resolve", params={"telegram_id": telegram_id})


def get_profile(client: ApiClient, telegram_id: int) -> dict:
    return client.get(f"{_PREFIX}/profile", params={"telegram_id": telegram_id})


def get_stats(client: ApiClient, telegram_id: int) -> dict:
    return client.get(f"{_PREFIX}/stats", params={"telegram_id": telegram_id})


def compare(client: ApiClient, telegram_id: int, opponent_id: int) -> dict:
    return client.get(
        f"{_PREFIX}/compare",
        params={"telegram_id": telegram_id, "opponent_id": opponent_id},
    )

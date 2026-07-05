from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_balance(client: ApiClient, telegram_id: int) -> dict:
    return client.get(f"{_PREFIX}/economy/balance", params={"telegram_id": telegram_id})


def get_economy_history(client: ApiClient, telegram_id: int, limit: int = 5) -> list:
    return client.get(
        f"{_PREFIX}/economy/history", params={"telegram_id": telegram_id, "limit": limit},
    )

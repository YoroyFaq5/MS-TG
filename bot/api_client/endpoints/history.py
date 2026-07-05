from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_history(client: ApiClient, telegram_id: int, page: int = 1, per_page: int = 10) -> dict:
    return client.get(
        f"{_PREFIX}/history",
        params={"telegram_id": telegram_id, "page": page, "per_page": per_page},
    )

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def unlink(client: ApiClient, telegram_id: int) -> dict:
    return client.post(f"{_PREFIX}/account/unlink", json={"telegram_id": telegram_id})

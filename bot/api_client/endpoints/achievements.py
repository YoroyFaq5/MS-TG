from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_achievements(client: ApiClient, telegram_id: int) -> list:
    return client.get(f"{_PREFIX}/achievements", params={"telegram_id": telegram_id})


def pin(client: ApiClient, telegram_id: int, achievement_id: int) -> None:
    return client.post(
        f"{_PREFIX}/achievements/{achievement_id}/pin", json={"telegram_id": telegram_id},
    )


def unpin(client: ApiClient, telegram_id: int, achievement_id: int) -> None:
    return client.post(
        f"{_PREFIX}/achievements/{achievement_id}/unpin", json={"telegram_id": telegram_id},
    )


def get_titles(client: ApiClient, telegram_id: int) -> list:
    return client.get(f"{_PREFIX}/titles", params={"telegram_id": telegram_id})

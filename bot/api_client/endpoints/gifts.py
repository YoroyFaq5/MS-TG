from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_inbox(client: ApiClient, telegram_id: int, page: int = 1, per_page: int = 10) -> dict:
    return client.get(
        f"{_PREFIX}/gifts/inbox", params={"telegram_id": telegram_id, "page": page, "per_page": per_page},
    )


def get_history(client: ApiClient, telegram_id: int, page: int = 1, per_page: int = 10) -> dict:
    return client.get(
        f"{_PREFIX}/gifts/history", params={"telegram_id": telegram_id, "page": page, "per_page": per_page},
    )


def get_giftable_items(client: ApiClient, telegram_id: int) -> list:
    return client.get(f"{_PREFIX}/gifts/giftable-items", params={"telegram_id": telegram_id})


def send_gift(
    client: ApiClient, telegram_id: int, inventory_item_id: int, to_player_id: int,
    message: Optional[str] = None,
) -> dict:
    return client.post(f"{_PREFIX}/gifts/send", json={
        "telegram_id": telegram_id, "inventory_item_id": inventory_item_id,
        "to_player_id": to_player_id, "message": message,
    })

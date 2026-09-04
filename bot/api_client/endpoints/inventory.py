from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_inventory(client: ApiClient, telegram_id: int, category: Optional[str] = None) -> list:
    params = {"telegram_id": telegram_id}
    if category:
        params["category"] = category
    return client.get(f"{_PREFIX}/inventory", params=params)


def equip(client: ApiClient, telegram_id: int, inventory_item_id: int) -> dict:
    return client.post(f"{_PREFIX}/inventory/{inventory_item_id}/equip", json={"telegram_id": telegram_id})


def unequip(client: ApiClient, telegram_id: int, inventory_item_id: int) -> dict:
    return client.post(f"{_PREFIX}/inventory/{inventory_item_id}/unequip", json={"telegram_id": telegram_id})

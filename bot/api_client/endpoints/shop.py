from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_items(
    client: ApiClient, category: Optional[str] = None, sort: Optional[str] = None,
    telegram_id: Optional[int] = None, page: int = 1, per_page: int = 8,
) -> dict:
    params = {"page": page, "per_page": per_page}
    if category:
        params["category"] = category
    if sort:
        params["sort"] = sort
    if telegram_id:
        params["telegram_id"] = telegram_id
    return client.get(f"{_PREFIX}/shop/items", params=params)


def get_item_detail(client: ApiClient, item_id: int, telegram_id: Optional[int] = None) -> dict:
    params = {"telegram_id": telegram_id} if telegram_id else None
    return client.get(f"{_PREFIX}/shop/items/{item_id}", params=params)


def buy_item(client: ApiClient, telegram_id: int, item_id: int) -> dict:
    return client.post(f"{_PREFIX}/shop/items/{item_id}/buy", json={"telegram_id": telegram_id})

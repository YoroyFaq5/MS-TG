from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_tournaments(
    client: ApiClient, status: Optional[str] = None, type_: Optional[str] = None,
    page: int = 1, per_page: int = 10,
) -> dict:
    params = {"page": page, "per_page": per_page}
    if status:
        params["status"] = status
    if type_:
        params["type"] = type_
    return client.get(f"{_PREFIX}/tournaments", params=params)


def get_tournament_detail(client: ApiClient, tournament_id: int, telegram_id: Optional[int] = None) -> dict:
    params = {"telegram_id": telegram_id} if telegram_id else None
    return client.get(f"{_PREFIX}/tournaments/{tournament_id}", params=params)

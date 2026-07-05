from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_tournaments(
    client: ApiClient, status: Optional[str] = None, page: int = 1, per_page: int = 10,
) -> dict:
    params = {"page": page, "per_page": per_page}
    if status:
        params["status"] = status
    return client.get(f"{_PREFIX}/tournaments", params=params)


def get_tournament_detail(client: ApiClient, tournament_id: int) -> dict:
    return client.get(f"{_PREFIX}/tournaments/{tournament_id}")

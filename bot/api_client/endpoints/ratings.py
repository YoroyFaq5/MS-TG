from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_ratings(
    client: ApiClient,
    scope: str = "global",
    page: int = 1,
    per_page: int = 10,
    season_id: Optional[int] = None,
    year: Optional[int] = None,
) -> dict:
    params = {"scope": scope, "page": page, "per_page": per_page}
    if season_id is not None:
        params["season_id"] = season_id
    if year is not None:
        params["year"] = year
    return client.get(f"{_PREFIX}/ratings", params=params)

from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_current_season(client: ApiClient) -> Optional[dict]:
    return client.get(f"{_PREFIX}/seasons/current")


def get_seasons(client: ApiClient, year: Optional[int] = None) -> dict:
    params = {"year": year} if year else None
    return client.get(f"{_PREFIX}/seasons", params=params)


def get_season_detail(client: ApiClient, season_id: int, page: int = 1, per_page: int = 10) -> dict:
    return client.get(
        f"{_PREFIX}/seasons/{season_id}", params={"page": page, "per_page": per_page},
    )


def get_my_place(client: ApiClient, telegram_id: int, season_id: int) -> dict:
    return client.get(
        f"{_PREFIX}/seasons/{season_id}/my-place", params={"telegram_id": telegram_id},
    )


def get_season_winners(client: ApiClient, page: int = 1, per_page: int = 10) -> dict:
    return client.get(
        f"{_PREFIX}/seasons/winners", params={"page": page, "per_page": per_page},
    )

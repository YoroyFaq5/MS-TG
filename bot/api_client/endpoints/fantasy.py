from typing import Optional

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def _scope_params(telegram_id, tournament_id, tournament_series_id=None, is_practice=False):
    params = {"telegram_id": telegram_id, "tournament_id": tournament_id}
    if tournament_series_id:
        params["tournament_series_id"] = tournament_series_id
    if is_practice:
        params["is_practice"] = "1"
    return params


def get_events(client: ApiClient, telegram_id: Optional[int] = None) -> dict:
    params = {"telegram_id": telegram_id} if telegram_id else None
    return client.get(f"{_PREFIX}/fantasy/events", params=params)


def get_history(client: ApiClient, telegram_id: int, page: int = 1, per_page: int = 10) -> dict:
    return client.get(
        f"{_PREFIX}/fantasy/history", params={"telegram_id": telegram_id, "page": page, "per_page": per_page},
    )


def get_draft_by_id(client: ApiClient, telegram_id: int, draft_id: int) -> dict:
    return client.get(f"{_PREFIX}/fantasy/draft/{draft_id}", params={"telegram_id": telegram_id})


def get_my_draft(
    client: ApiClient, telegram_id: int, tournament_id: int,
    tournament_series_id: Optional[int] = None, is_practice: bool = False,
) -> dict:
    return client.get(
        f"{_PREFIX}/fantasy/my",
        params=_scope_params(telegram_id, tournament_id, tournament_series_id, is_practice),
    )


def create_draft(
    client: ApiClient, telegram_id: int, tournament_id: int,
    tournament_series_id: Optional[int] = None, is_practice: bool = False,
) -> dict:
    return client.post(f"{_PREFIX}/fantasy/draft", json={
        "telegram_id": telegram_id, "tournament_id": tournament_id,
        "tournament_series_id": tournament_series_id, "is_practice": is_practice,
    })


def add_pick(client: ApiClient, telegram_id: int, draft_id: int, player_id: int) -> dict:
    return client.post(
        f"{_PREFIX}/fantasy/pick",
        json={"telegram_id": telegram_id, "draft_id": draft_id, "player_id": player_id},
    )


def remove_pick(client: ApiClient, telegram_id: int, draft_id: int, player_id: int) -> dict:
    return client.delete(
        f"{_PREFIX}/fantasy/pick",
        json={"telegram_id": telegram_id, "draft_id": draft_id, "player_id": player_id},
    )


def cancel_draft(client: ApiClient, telegram_id: int, draft_id: int) -> dict:
    return client.post(f"{_PREFIX}/fantasy/draft/{draft_id}/cancel", json={"telegram_id": telegram_id})


def get_leaderboard(
    client: ApiClient, tournament_id: int, tournament_series_id: Optional[int] = None,
    group_number: Optional[int] = None, is_practice: bool = False,
) -> list:
    params = _scope_params(None, tournament_id, tournament_series_id, is_practice)
    params.pop("telegram_id")
    if group_number is not None:
        params["group_number"] = group_number
    return client.get(f"{_PREFIX}/fantasy/leaderboard", params=params)


def get_available(
    client: ApiClient, telegram_id: int, tournament_id: int,
    tournament_series_id: Optional[int] = None, is_practice: bool = False,
) -> list:
    return client.get(
        f"{_PREFIX}/fantasy/available",
        params=_scope_params(telegram_id, tournament_id, tournament_series_id, is_practice),
    )

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_my_draft(client: ApiClient, telegram_id: int, tournament_id: int) -> dict:
    return client.get(
        f"{_PREFIX}/fantasy/my",
        params={"telegram_id": telegram_id, "tournament_id": tournament_id},
    )


def create_draft(client: ApiClient, telegram_id: int, tournament_id: int) -> dict:
    return client.post(
        f"{_PREFIX}/fantasy/draft",
        json={"telegram_id": telegram_id, "tournament_id": tournament_id},
    )


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


def get_leaderboard(client: ApiClient, tournament_id: int) -> list:
    return client.get(f"{_PREFIX}/fantasy/leaderboard", params={"tournament_id": tournament_id})


def get_available(client: ApiClient, telegram_id: int, tournament_id: int) -> list:
    return client.get(
        f"{_PREFIX}/fantasy/available",
        params={"telegram_id": telegram_id, "tournament_id": tournament_id},
    )

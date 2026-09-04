from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def search_players(client: ApiClient, query: str, fast: bool = False) -> list:
    return client.get(f"{_PREFIX}/players/search", params={"q": query}, fast=fast)


def get_player(client: ApiClient, player_id: int) -> dict:
    return client.get(f"{_PREFIX}/players/{player_id}")


def compare_players(client: ApiClient, player_id_a: int, player_id_b: int, fast: bool = False) -> dict:
    return client.get(
        f"{_PREFIX}/players/compare", params={"a": player_id_a, "b": player_id_b}, fast=fast,
    )

from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def search_players(client: ApiClient, query: str) -> list:
    return client.get(f"{_PREFIX}/players/search", params={"q": query})


def compare_players(client: ApiClient, player_id_a: int, player_id_b: int) -> dict:
    return client.get(f"{_PREFIX}/players/compare", params={"a": player_id_a, "b": player_id_b})

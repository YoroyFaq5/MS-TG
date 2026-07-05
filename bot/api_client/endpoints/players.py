from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def search_players(client: ApiClient, query: str) -> list:
    return client.get(f"{_PREFIX}/players/search", params={"q": query})

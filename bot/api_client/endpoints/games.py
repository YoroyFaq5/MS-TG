from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_game_detail(client: ApiClient, game_id: int) -> dict:
    return client.get(f"{_PREFIX}/games/{game_id}")

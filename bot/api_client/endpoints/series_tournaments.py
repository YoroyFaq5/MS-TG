from bot.api_client.client import ApiClient

_PREFIX = "/api/v1/bot"


def get_series_tournaments(client: ApiClient) -> list:
    return client.get(f"{_PREFIX}/series-tournaments")


def get_series_tournament_detail(client: ApiClient, series_tournament_id: int) -> dict:
    return client.get(f"{_PREFIX}/series-tournaments/{series_tournament_id}")


def get_series_evening_detail(client: ApiClient, series_tournament_id: int, series_id: int) -> dict:
    return client.get(f"{_PREFIX}/series-tournaments/{series_tournament_id}/series/{series_id}")


def get_series_shortcut(client: ApiClient, series_id: int) -> dict:
    """Resolve a bare series_id (as carried in Fantasy's compact scope
    callback_data) to its name + parent series_tournament_id/tournament_id."""
    return client.get(f"{_PREFIX}/series/{series_id}")

"""
ApiClient
=========
Единственное место во всём боте, которое знает про HTTP к основному сайту.
Хендлеры и сервисы никогда не дёргают requests напрямую — только через
методы этого класса (или через endpoints/*, которые появятся вместе с
конкретными фичами в следующих этапах).

Авторизация — серверный токен бота (Authorization: Bearer) на каждый
запрос, никогда не виден конечному пользователю. Конкретный игрок
передаётся отдельным параметром telegram_id — сайт сам резолвит его
в player_id через колонку Player.telegram_id.

Ретраи — только на сетевые ошибки и 5xx (по умолчанию поведение urllib3
Retry), не на 4xx: 4xx — это осмысленная ошибка клиента (не найден,
не авторизован), повторный запрос её не исправит.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.api_client.exceptions import (
    ApiError, ApiNotFound, ApiServerError, ApiTimeout, ApiUnauthorized,
)

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(
        self,
        base_url: str,
        service_token: str,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = (connect_timeout, read_timeout)

        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {service_token}"
        retry = Retry(
            total=2, backoff_factor=0.5,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=("GET", "POST", "DELETE"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(method, url, timeout=self._timeout, **kwargs)
        except requests.Timeout as e:
            logger.warning("API timeout: %s %s", method, path)
            raise ApiTimeout(str(e)) from e
        except requests.RequestException as e:
            logger.warning("API network error: %s %s — %s", method, path, e)
            raise ApiError(str(e)) from e

        if resp.status_code == 401 or resp.status_code == 403:
            raise ApiUnauthorized(f"{method} {path} -> {resp.status_code}")
        if resp.status_code == 404:
            raise ApiNotFound(f"{method} {path} -> 404")
        if resp.status_code >= 500:
            raise ApiServerError(f"{method} {path} -> {resp.status_code}")
        if resp.status_code >= 400:
            raise ApiError(f"{method} {path} -> {resp.status_code}: {resp.text[:200]}")

        if not resp.content:
            return None
        return resp.json()

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("POST", path, json=json)

    def delete(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("DELETE", path, json=json)

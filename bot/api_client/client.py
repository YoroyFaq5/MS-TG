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
        fast_connect_timeout: float = 2.0,
        fast_read_timeout: float = 3.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = (connect_timeout, read_timeout)
        self._fast_timeout = (fast_connect_timeout, fast_read_timeout)

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

        # Отдельная сессия без ретраев и с коротким таймаутом — для
        # time-sensitive путей вроде инлайн-режима, где у Telegram есть
        # жёсткий дедлайн на ответ (answer_inline_query): лучше быстро
        # сдаться и откатиться на запасной вариант, чем тянуть с ретраями
        # и в итоге получить "query is too old" от Telegram.
        self.fast_session = requests.Session()
        self.fast_session.headers["Authorization"] = f"Bearer {service_token}"
        fast_adapter = HTTPAdapter(max_retries=Retry(total=0))
        self.fast_session.mount("https://", fast_adapter)
        self.fast_session.mount("http://", fast_adapter)

    @staticmethod
    def _extract_error_message(resp) -> Optional[str]:
        try:
            body = resp.json()
        except ValueError:
            return resp.text[:200] or None
        if isinstance(body, dict) and body.get("message"):
            return body["message"]
        return resp.text[:200] or None

    def _request(self, method: str, path: str, fast: bool = False, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        session = self.fast_session if fast else self.session
        timeout = self._fast_timeout if fast else self._timeout
        try:
            resp = session.request(method, url, timeout=timeout, **kwargs)
        except requests.Timeout as e:
            logger.warning("API timeout: %s %s", method, path)
            raise ApiTimeout(str(e)) from e
        except requests.RequestException as e:
            logger.warning("API network error: %s %s — %s", method, path, e)
            raise ApiError(str(e)) from e

        if resp.status_code >= 400:
            # MS кладёт человекочитаемое сообщение business-логики в JSON
            # {"status":"error","message":...} даже для 4xx (см. api_bot.py
            # _fail) — вытаскиваем именно его, а не сырой текст ответа,
            # иначе пользователь в Telegram увидел бы кусок JSON вместо
            # "уже есть драфт для этого турнира".
            message = self._extract_error_message(resp) or f"{method} {path} -> {resp.status_code}"
            if resp.status_code in (401, 403):
                raise ApiUnauthorized(message)
            if resp.status_code == 404:
                raise ApiNotFound(message)
            if resp.status_code >= 500:
                raise ApiServerError(message)
            raise ApiError(message)

        if not resp.content:
            return None
        body = resp.json()
        # MS оборачивает все ответы в {"status": "ok"/"error", "message",
        # "data"} — разворачиваем здесь один раз, чтобы endpoints/* и
        # presenters/* работали с самими данными, не с конвертом. Ошибки
        # уровня HTTP уже отловлены выше по коду статуса; status="error"
        # с кодом 200 в этом API не встречается (см. app/routes/api_bot.py
        # — _fail всегда передаёт свой HTTP-код), но на всякий случай
        # тоже поднимаем ApiError, а не отдаём вызывающему коду мусор.
        if isinstance(body, dict) and "status" in body and "data" in body:
            if body["status"] != "ok":
                raise ApiError(body.get("message", "Unknown API error"))
            return body["data"]
        return body

    def get(self, path: str, params: Optional[dict] = None, fast: bool = False) -> Any:
        return self._request("GET", path, params=params, fast=fast)

    def post(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("POST", path, json=json)

    def delete(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("DELETE", path, json=json)

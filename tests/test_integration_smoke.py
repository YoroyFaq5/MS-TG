"""
Reproducible cross-repo integration smoke test.

Spins up BOTH the MS (main site) Flask app and this repo's own Flask app as
real, live HTTP servers on localhost (via werkzeug's dev server in a
background thread — not Flask's in-process test client), and exercises the
actual wire contract between them:

- MS-TG -> MS:  GET/POST /api/v1/bot/* with `Authorization: Bearer
  <MAIN_API_SERVICE_TOKEN>` — through this repo's own real ApiClient/
  endpoints code, not raw `requests` calls, so the bot's real HTTP-client
  behaviour (retries, error mapping) is exercised too.
- MS -> MS-TG:  POST /events/<type> with `X-Signature` (HMAC-SHA256) and
  `X-Event-Id` — through MS's real NotifyOutboxService.enqueue()/drain(),
  landing on this repo's real Flask route.

Only the outbound Telegram Bot API call (bot.send_message) is mocked —
every request BETWEEN the two apps goes over a real TCP socket on
localhost, satisfying "real HTTP between the apps, mock only the Telegram
send" from the task brief.

ASSUMPTIONS (explicit, not silently relied on):

1. The MS repo is checked out as a SIBLING directory of this one, i.e.
   `<parent>/MS` next to `<parent>/MS-TG` — exactly how these two repos
   are normally cloned side by side for local development on this
   project.
2. The Python environment running this test has BOTH repos' dependencies
   installed — neither repo's own requirements.txt includes the other's
   (MS-TG doesn't need Flask-SQLAlchemy/PyMySQL/etc. for its own code, MS
   doesn't need pyTelegramBotAPI). Running this file under either repo's
   normal venv will fail to import the other side. Build a dedicated venv
   once:

       cd MS-TG
       python -m venv .venv-integration
       .venv-integration/Scripts/activate  (Windows) or source .../bin/activate
       pip install -r requirements.txt -r ../MS/requirements.txt pytest

   then run: .venv-integration/Scripts/python.exe -m pytest tests/test_integration_smoke.py -v

If either assumption doesn't hold, the whole module is SKIPPED (not
failed) with a message explaining which one — so the rest of this repo's
suite still runs standalone under its own normal venv (e.g. a CI checkout
of MS-TG alone has no way to exercise the other side of the contract).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import socket
import sys
import threading
import time
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

_MS_REPO = Path(__file__).resolve().parents[2] / "MS"
if not (_MS_REPO / "app" / "__init__.py").exists():
    pytest.skip(
        f"MS repo not found at {_MS_REPO} (expected as a sibling directory "
        f"of MS-TG) — skipping the cross-repo integration smoke test.",
        allow_module_level=True,
    )

sys.path.insert(0, str(_MS_REPO))

try:
    import flask_sqlalchemy  # noqa: F401  — MS's own dependency, not MS-TG's
except ImportError:
    pytest.skip(
        "MS's dependencies (e.g. flask_sqlalchemy) aren't installed in this "
        "Python environment — this test needs a combined venv with both "
        "repos' requirements.txt installed. See the module docstring above "
        "for the exact setup commands.",
        allow_module_level=True,
    )

# Frozen into bot.config.Config / bot.telegram_bot.api_client the first time
# anything under bot.* was imported in this test session (tests/conftest.py
# sets these via os.environ.setdefault before any test module runs) — reuse
# the SAME values on MS's side below so both apps agree on the shared
# secret/token without needing to touch either app's already-frozen config.
SHARED_TOKEN = os.environ["MAIN_API_SERVICE_TOKEN"]
SHARED_SECRET = os.environ["INCOMING_EVENT_SECRET"]


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_reachable(url: str, timeout: float = 5.0) -> None:
    """Poll until the socket accepts a connection and returns SOME HTTP
    response — a 401/404 still proves the server is up; only a connection-
    level failure means it isn't ready yet."""
    deadline = time.monotonic() + timeout
    last_exc = None
    while time.monotonic() < deadline:
        try:
            requests.get(url, timeout=0.5)
            return
        except requests.RequestException as e:
            last_exc = e
            time.sleep(0.05)
    raise RuntimeError(f"Server at {url} did not come up in time") from last_exc


def _sign(body: bytes, secret: str = SHARED_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@pytest.fixture(scope="module")
def ms_server(tmp_path_factory):
    """The real MS Flask app, served over a live TCP port."""
    tmp_dir = tmp_path_factory.mktemp("ms_integration")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_dir / 'ms.db'}"
    os.environ.setdefault("SECRET_KEY", "integration-test-secret")

    from app import create_app as create_ms_app
    from app import db as ms_db

    app = create_ms_app("development")
    # Set directly on the instance rather than relying on env-var timing —
    # app/config.py's Config class attributes were already frozen at
    # whatever env state existed the moment `app.config` was first
    # imported; every route reads current_app.config at request time, so
    # this override is what actually takes effect.
    app.config["MAIN_API_SERVICE_TOKEN"] = SHARED_TOKEN
    app.config["INCOMING_EVENT_SECRET"] = SHARED_SECRET
    with app.app_context():
        ms_db.create_all()

    from werkzeug.serving import make_server

    port = _free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    _wait_until_reachable(f"{base_url}/api/v1/bot/seasons/current")

    try:
        yield app, base_url, ms_db
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture(scope="module")
def bot_server():
    """The real MS-TG (bot) Flask app, served over a live TCP port."""
    from bot import create_app as create_bot_app

    app = create_bot_app("default")
    app.config["INCOMING_EVENT_SECRET"] = SHARED_SECRET

    from werkzeug.serving import make_server

    port = _free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    _wait_until_reachable(f"{base_url}/health")

    try:
        yield app, base_url
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture()
def ms_api_client(ms_server):
    """The bot's OWN ApiClient singleton (bot/telegram_bot.py), temporarily
    redirected at the live MS server started above for this one test, then
    restored — it's a process-wide singleton normally frozen at whatever
    MAIN_API_BASE_URL/MAIN_API_SERVICE_TOKEN were in the environment the
    first time bot.telegram_bot was imported (a dummy value from this
    repo's own tests/conftest.py, not a live server)."""
    import bot.telegram_bot as telegram_bot_module

    _, ms_base_url, _ = ms_server
    old_base_url = telegram_bot_module.api_client.base_url
    telegram_bot_module.api_client.base_url = ms_base_url
    try:
        yield telegram_bot_module.api_client
    finally:
        telegram_bot_module.api_client.base_url = old_base_url


@pytest.fixture()
def mock_send_message():
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        yield mock_send


def _make_tournament(ms_db, name: str, status: str = "active"):
    from app.models import Tournament, TournamentType
    t = Tournament(name=name, type=TournamentType.INDIVIDUAL, is_ranked=True, has_stages=False, status=status)
    ms_db.session.add(t)
    ms_db.session.commit()
    return t


def _make_player(ms_db, name: str, telegram_id: str | None = None):
    from app.models import Player
    p = Player(name=name, nickname=name, is_active=True, elo=1000.0)
    if telegram_id:
        p.telegram_id = telegram_id
    ms_db.session.add(p)
    ms_db.session.commit()
    return p


# ── MS-TG -> MS: Bearer-token auth over real HTTP ───────────────────────────

def test_bot_calls_ms_bot_api_with_bearer_token_over_real_http(ms_api_client):
    from bot.api_client.endpoints.seasons import get_current_season

    result = get_current_season(ms_api_client)  # no active season fixture -> None, but a real 200 round trip
    assert result is None


def test_wrong_bearer_token_is_rejected_by_ms(ms_server):
    from bot.api_client.client import ApiClient
    from bot.api_client.exceptions import ApiUnauthorized
    from bot.api_client.endpoints.seasons import get_current_season

    _, ms_base_url, _ = ms_server
    bad_client = ApiClient(base_url=ms_base_url, service_token="definitely-wrong-token")
    with pytest.raises(ApiUnauthorized):
        get_current_season(bad_client)


def test_missing_bearer_token_is_rejected_by_ms(ms_server):
    _, ms_base_url, _ = ms_server
    resp = requests.get(f"{ms_base_url}/api/v1/bot/seasons/current", timeout=2)
    assert resp.status_code == 401


# ── Hidden tournament standings are not leaked via the real bot API ────────

def test_hidden_standings_not_leaked_over_real_http(ms_server, ms_api_client):
    from bot.api_client.endpoints.tournaments import get_tournament_detail

    ms_app, _, ms_db = ms_server
    with ms_app.app_context():
        t = _make_tournament(ms_db, "Integration Hidden Cup")
        t.hide_standings = True
        ms_db.session.commit()
        tournament_id = t.id

    data = get_tournament_detail(ms_api_client, tournament_id)  # real HTTP — no app context needed here
    assert data["can_view_standings"] is False
    assert data["player_ratings"] == []
    assert data["team_ratings"] == []


# ── A mutating endpoint can't act on someone else's resource ───────────────

def test_gift_send_rejects_someone_elses_inventory_item_over_real_http(ms_server, ms_api_client):
    from app.models import ShopItem, InventoryItem, ShopCategory, Rarity
    from bot.api_client.endpoints.gifts import send_gift
    from bot.api_client.exceptions import ApiError

    ms_app, _, ms_db = ms_server
    with ms_app.app_context():
        owner = _make_player(ms_db, "IntegrationOwner")
        _make_player(ms_db, "IntegrationAttacker", telegram_id="900000111")

        item = ShopItem(
            name="Integration Frame", category=ShopCategory.PROFILE_CUSTOMIZATION,
            subcategory="frame", rarity=Rarity.COMMON, price=10.0,
        )
        ms_db.session.add(item)
        ms_db.session.flush()
        inv = InventoryItem(player_id=owner.id, item_id=item.id, price_paid=10.0)
        ms_db.session.add(inv)
        ms_db.session.commit()
        owner_id, inv_id = owner.id, inv.id

    with pytest.raises(ApiError):
        send_gift(ms_api_client, telegram_id=900000111, inventory_item_id=inv_id, to_player_id=owner_id)

    with ms_app.app_context():
        inv = ms_db.session.get(InventoryItem, inv_id)
        assert inv.player_id == owner_id, "ownership must not have changed"


# ── MS -> MS-TG: HMAC + X-Event-Id auth over real HTTP ──────────────────────

def test_ms_delivers_event_to_bot_over_real_http_and_bot_sends_once(
    ms_server, bot_server, mock_send_message,
):
    from app.services.notify_outbox_service import NotifyOutboxService

    ms_app, _, ms_db = ms_server
    _, bot_base_url = bot_server
    ms_app.config["BOT_EVENTS_URL"] = bot_base_url

    with ms_app.app_context():
        NotifyOutboxService.enqueue("title-granted", {"telegram_id": "900000222", "title_name": "Легенда"})
        ms_db.session.commit()
        summary = NotifyOutboxService.drain()

    assert summary["delivered"] == 1
    mock_send_message.assert_called_once()
    assert mock_send_message.call_args[0][0] == 900000222
    assert "Легенда" in mock_send_message.call_args[0][1]


def test_wrong_hmac_signature_rejected_by_bot_over_real_http(bot_server, mock_send_message):
    _, bot_base_url = bot_server
    body = b'{"telegram_id": "900000333", "title_name": "Forged"}'

    resp = requests.post(
        f"{bot_base_url}/events/title-granted",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": "0" * 64,  # well-formed hex, but not HMAC(body, secret)
            "X-Event-Id": "integration-smoke-forged-1",
        },
        timeout=2,
    )
    assert resp.status_code == 403
    mock_send_message.assert_not_called()


def test_missing_hmac_signature_rejected_by_bot_over_real_http(bot_server, mock_send_message):
    _, bot_base_url = bot_server
    body = b'{"telegram_id": "900000333", "title_name": "Forged"}'

    resp = requests.post(f"{bot_base_url}/events/title-granted", data=body, timeout=2)
    assert resp.status_code == 403
    mock_send_message.assert_not_called()


def test_repeated_event_id_does_not_send_a_second_message(bot_server, mock_send_message):
    """Simulates the realistic retry scenario the outbox's dedup exists
    for: the site's POST is delivered and processed, but the ack is lost
    (network blip) so the outbox retries the SAME event_id — the bot must
    not send a second Telegram message for it."""
    _, bot_base_url = bot_server
    body = b'{"telegram_id": "900000444", "title_name": "Repeatable"}'
    headers = {
        "Content-Type": "application/json",
        "X-Signature": _sign(body),
        "X-Event-Id": "integration-smoke-retry-1",
    }

    first = requests.post(f"{bot_base_url}/events/title-granted", data=body, headers=headers, timeout=2)
    second = requests.post(f"{bot_base_url}/events/title-granted", data=body, headers=headers, timeout=2)

    assert first.status_code == 200
    assert "duplicate" not in first.json()
    assert second.status_code == 200
    assert second.json().get("duplicate") is True
    mock_send_message.assert_called_once()
    assert mock_send_message.call_args[0][0] == 900000444

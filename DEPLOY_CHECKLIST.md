# Чеклист первого деплоя (MS + MS-TG)

Один шаблон для обоих проектов — MS (основной сайт) обновляется, MS-TG
(бот) разворачивается впервые. Каждый пункт — с конкретной командой
проверки, а не только описанием.

## 1. Миграции

**MS** — таблица `notify_outbox_events` (см.
`migrations/versions/c3e5b9f02a13_notify_outbox_events.py` и
`migrate_notify_outbox.py`), плюс всё из `CLAUDE_TASKS.md`
(`gg_weight`, `qualified_via_season_id`), если ещё не применено:

```bash
cd MS
source venv/bin/activate  # или venv/Scripts/activate на Windows
python migrate_season_gg_weight.py
python migrate_tournament_participant_qualified_season.py
python migrate_notify_outbox.py
```

Каждый скрипт идемпотентен (проверяет `information_schema` перед
изменением) — безопасно запускать повторно, в том числе если часть уже
применена.

**MS-TG** — миграций в привычном смысле нет (нет Alembic/файлов
`migrate_*.py`): единственное состояние — локальный SQLite-файл
`bot/data/bot.db` (или путь из `BOT_DB_PATH`). `storage.init_db()`
создаёт всю схему при первом запуске `create_app()` и САМ применяет одну
встроенную схемную миграцию при обновлении с более старой версии —
`fsm_state` перешла с `PRIMARY KEY (chat_id)` на составной
`PRIMARY KEY (chat_id, telegram_user_id)` (нужно для корректного FSM в
группах — раньше одно состояние на чат путало бы FSM двух разных
пользователей). Миграция идемпотентна (проверяет наличие колонки
`telegram_user_id` через `PRAGMA table_info`, ничего не делает при
повторном запуске) и **не требует ручных действий** — просто выполняется
при следующем старте процесса, старые строки переносятся с допущением
`telegram_user_id = chat_id` (верно для всей истории до этого момента,
т.к. FSM раньше был доступен только в личных чатах, где `chat_id ==
telegram_user_id`). Убедиться, что процесс имеет права на запись в
директорию файла:

```bash
mkdir -p bot/data && touch bot/data/bot.db && rm bot/data/bot.db  # проверка прав, файл создаст сам процесс
```

## 2. Обязательные переменные окружения

**MS** (см. `.env.example`) — для интеграции с ботом:

| Переменная | Обязательна? | Назначение |
|---|---|---|
| `BOT_EVENTS_URL` | нет (фича тихо выключена без неё) | базовый URL бота, куда `NotifyOutboxService` шлёт события |
| `INCOMING_EVENT_SECRET` | да, если задан `BOT_EVENTS_URL` | общий HMAC-секрет, ДОЛЖЕН совпадать с тем же на стороне бота |
| `MAIN_API_SERVICE_TOKEN` | да, иначе `/api/v1/bot/*` отвечает 503 | Bearer-токен, ДОЛЖЕН совпадать с `MAIN_API_SERVICE_TOKEN` бота |
| `TELEGRAM_BOT_USERNAME` | нет | нужен только для кнопок "Открыть в боте" (`telegram_deep_link`) |
| `OUTBOX_WORKER_ENABLED` | нет | см. п.3 — фоновый поток вместо cron |
| `OUTBOX_POLL_SECONDS` | нет (default 15) | интервал фонового потока |

**MS-TG** (см. `.env.example`) — ВСЕ обязательны, приложение не
запустится без них (тихого fallback нет по дизайну, см. `bot/config.py`):

- `TELEGRAM_BOT_TOKEN` — от @BotFather.
- `TELEGRAM_WEBHOOK_SECRET` — придумать длинную случайную строку.
- `TELEGRAM_WEBHOOK_PATH_TOKEN` — придумать случайный сегмент пути.
- `MAIN_API_BASE_URL` — `https://<домен-основного-сайта>`.
- `MAIN_API_SERVICE_TOKEN` — **тот же самый** токен, что в `MAIN_API_SERVICE_TOKEN` на MS.
- `INCOMING_EVENT_SECRET` — **тот же самый** секрет, что в `INCOMING_EVENT_SECRET` на MS.

Опционально: `BOT_DB_PATH`, `API_CONNECT_TIMEOUT`, `API_READ_TIMEOUT`,
`TELEGRAM_BOT_USERNAME` (кнопки "Открыть в боте" из группового чата — без
неё бот один раз спросит своё имя через `bot.get_me()` и закеширует),
`GROUP_COMMAND_LIMIT_SHORT`/`GROUP_COMMAND_WINDOW_SHORT_SECONDS`/
`GROUP_COMMAND_LIMIT_LONG`/`GROUP_COMMAND_WINDOW_LONG_SECONDS` (антиспам
публичных команд `/top`, `/season`, `/tournaments`, `/player`,
`/compare`, `/game`, `/help` в группах — есть безопасный дефолт).

Проверка перед запуском:

```bash
python -c "from bot.config import Config; print('OK', Config.TELEGRAM_BOT_TOKEN[:8] + '...')"
```

Если что-то не задано, процесс упадёт с понятным `RuntimeError` сразу
здесь, а не при первом реальном запросе.

## 3. Запуск web-процесса и outbox worker

**MS** — обычный gunicorn/systemd, без изменений в способе запуска.
Доставку очереди уведомлений включить ОДНИМ из двух способов (не обоими
сразу — иначе события будут доставляться по два раза гонкой, хоть outbox
и защищён атомарным `UPDATE ... WHERE status='pending'` от дублей,
лишняя нагрузка не нужна):

- **Вариант А (проще):** `OUTBOX_WORKER_ENABLED=true` в окружении
  web-процесса — фоновый поток внутри каждого gunicorn worker'а,
  сам поллит раз в `OUTBOX_POLL_SECONDS`. Безопасно при нескольких
  worker'ах (см. п.1 про атомарный claim).
- **Вариант Б (cron):** `flask outbox-drain` по расписанию (например,
  раз в минуту) вместо фонового потока — не задавать
  `OUTBOX_WORKER_ENABLED`.

**MS-TG** — тот же gunicorn/WSGI-паттерн, что у MS. Один момент:
`bot/__init__.py::create_app()` регистрирует вебхук-роут по пути
`/telegram/webhook/<TELEGRAM_WEBHOOK_PATH_TOKEN>` — сначала подставляется
переменная окружения, поэтому она должна быть задана ДО старта процесса
(что и так требуется п.2).

## 4. Health checks

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://<MS-домен>/           # ожидаем 200
curl -s -o /dev/null -w '%{http_code}\n' https://<MS-TG-домен>/health   # ожидаем 200, {"status":"ok"}
```

## 5. Установка Telegram-вебхука

```bash
curl -F "url=https://<MS-TG-домен>/telegram/webhook/<TELEGRAM_WEBHOOK_PATH_TOKEN>" \
     -F "secret_token=<TELEGRAM_WEBHOOK_SECRET>" \
     "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook"
```

Ответ должен быть `{"ok":true,"result":true,...}`.

## 6. Проверка webhook secret

```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

Убедиться, что `url` совпадает с ожидаемым и `last_error_message`
отсутствует. Дополнительно — что случайный POST без заголовка
`X-Telegram-Bot-Api-Secret-Token` отклоняется:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
     https://<MS-TG-домен>/telegram/webhook/<TELEGRAM_WEBHOOK_PATH_TOKEN>
# ожидаем 403
```

## 6б. Регистрация команд Telegram (`/`-меню)

Разные списки команд для личных и групповых чатов
(`BotCommandScopeAllPrivateChats`/`BotCommandScopeAllGroupChats`, см.
`bot/commands.py`) — выполнить один раз после каждого деплоя, который
добавляет/переименовывает команду (идемпотентно, безопасно запускать
повторно на каждом деплое "на всякий случай"):

```bash
flask set-commands
```

Ожидаемый вывод: `Telegram commands: {'private': 'updated'|'unchanged',
'group': 'updated'|'unchanged'}`. Проверить в самом Telegram: открыть "/"
в личном чате с ботом — должны быть только `/start` и `/help`; в любой
группе, куда добавлен бот, — все семь публичных команд.

## 7. Тестовый запрос к основному сайту (от бота)

С сервера бота (или откуда угодно, зная `MAIN_API_SERVICE_TOKEN`):

```bash
curl -s -H "Authorization: Bearer <MAIN_API_SERVICE_TOKEN>" \
     https://<MS-домен>/api/v1/bot/seasons/current
```

Ожидаем `{"status":"ok","data":{...}}` (или `data:null`, если сейчас нет
активного сезона) — НЕ 401/503.

## 8. Тестовое уведомление (от сайта к боту)

Проще всего — реальное действие на сайте, вызывающее
`BotNotifyService.notify_player(...)` (например, выдать себе тестовое
достижение через админку) на аккаунте с привязанным Telegram, затем:

```bash
flask outbox-drain           # если используется cron-вариант (п.3Б)
# или подождать OUTBOX_POLL_SECONDS, если включён фоновый поток (п.3А)
```

Проверить админку `/admin/analytics/outbox` на сайте — событие должно
перейти в статус `delivered`. Проверить, что сообщение реально пришло в
Telegram.

Альтернатива без реального игрока — прямой curl на бота с валидной
подписью (секрет = `INCOMING_EVENT_SECRET`):

```bash
BODY='{"telegram_id": "<ваш telegram_id>", "title_name": "Тест деплоя"}'
SIG=$(python3 -c "import hmac,hashlib,sys; print(hmac.new(sys.argv[1].encode(), sys.argv[2].encode(), hashlib.sha256).hexdigest())" "<INCOMING_EVENT_SECRET>" "$BODY")
curl -s -X POST "https://<MS-TG-домен>/events/title-granted" \
     -H "Content-Type: application/json" -H "X-Signature: $SIG" -H "X-Event-Id: manual-test-1" \
     -d "$BODY"
```

## 9. Откат (rollback)

**MS-TG (первый деплой):** если что-то пошло не так — самый безопасный
откат: снять Telegram-вебхук (бот перестаёт получать апдейты, сайт
продолжает копить события в `notify_outbox_events`, ничего не теряется),
разобраться, повторить деплой.

```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/deleteWebhook"
```

**MS (обновление):**

```bash
cd MS
git log --oneline -5              # найти предыдущий коммит
git checkout <предыдущий-коммит>  # или git revert <новый-коммит>
sudo systemctl restart ms-site
```

Миграции (`notify_outbox_events` и т.д.) откатывать НЕ нужно при простом
откате кода — новая таблица, ничего не ломает старый код, который её
просто не использует. Откатывать схему нужно только если сама миграция
была ошибочной (не этот случай).

## Rate limit — известное временное ограничение

`/api/v1/bot/*` использует **in-process** rate limiter (см.
`app/routes/api_bot.py`, `_rate_buckets`) — не распределённый. При
нескольких gunicorn worker'ах эффективный потолок кратно выше
заявленного (N worker'ов × лимит на worker). Это осознанно принятое
временное ограничение для одного узла — не блокер для первого деплоя,
но если сайт когда-нибудь уйдёт на несколько узлов за балансировщиком,
это надо будет заменить на Redis/nginx `limit_req` (уже отмечено как
follow-up в ARCHITECTURE.md бота).

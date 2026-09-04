# Changelog

## [Unreleased]

### Rewrite — MafiaTracker 2.0: full inline client, all remaining domains, security, outbox

Supersedes every "Вся полировка завершена" claim below — that was true only
for the command-based v1 client covering profile/stats/ratings/tournaments/
Fantasy(basic)/compare. This pass replaces the navigation model entirely and
fills in shop, inventory, gifts, notification settings, deep links, and a
durable outbox on the MS side. See ARCHITECTURE.md for the full picture;
summary of what changed:

**Security (increment 1)**
- Closed a real data leak: `GET /api/v1/bot/tournaments/<id>` on MS handed
  out `player_ratings`/`team_ratings` regardless of `Tournament.hide_standings`.
  Now mirrors the site's own `_can_view_standings` rule from a `telegram_id`
  param (hidden unless the caller is an admin who isn't themselves a
  participant) and returns `can_view_standings` explicitly.
- MS's Bot API: constant-time service-token comparison (`hmac.compare_digest`),
  a best-effort in-process rate limiter, and a request body size cap.
- Bot side: matching in-process rate limiter + `MAX_CONTENT_LENGTH` on both
  public endpoints (`/telegram/webhook/...`, `/events/<type>`).
- `bot/ui.py::esc()` — every presenter that interpolates a site-supplied
  string (display names, item/tournament/title names, gift notes, bios)
  into HTML parse_mode text now escapes it. Previously none did.

**Navigation shell (increment 2)**
- Inline hierarchical main menu (`bot/presenters/menu.py`,
  `bot/handlers/menu.py`) replaces the old flat Reply Keyboard — one
  compact "🏠 Меню" button is the only Reply Keyboard left; everything else
  edits the same message via inline keyboards. 9 sections per spec: Мой
  кабинет, Рейтинги, Турниры, Fantasy, Магазин, Инвентарь, Подарки,
  Сравнить игроков, Уведомления.
- `bot/keyboards/nav.py` — versioned callback_data (`v1:domain:action:...`),
  shared Home/Back footer, pagination row builder.
- `bot/dispatch.py::guarded_callback` — every new-domain handler is wrapped:
  swallows the pagination page-indicator no-op, rejects a double-tap on a
  `sensitive=True` action (purchase/gift/draft) via a short-lived lock, and
  guarantees exactly one `answer_callback_query` on any path a handler
  didn't reach itself.
- `bot/storage.py` — new local SQLite store (`bot/data/bot.db`, override via
  `BOT_DB_PATH`) for FSM state, double-tap locks, outbox event dedup, and
  per-category notification preferences. Chosen over Redis: this bot is a
  single small webhook-model Flask app with no other infra already
  running; SQLite needs zero new services and survives process restarts,
  unlike an in-memory dict. Revisit if the bot ever needs multiple
  concurrent app instances sharing this state.

**Seasons, tournaments, series, game cards (increment 3)**
- New MS endpoints: `/seasons/current`, `/seasons`, `/seasons/<id>`,
  `/seasons/<id>/my-place`, `/seasons/winners`, `/series-tournaments`,
  `/series-tournaments/<id>`, `/series-tournaments/<id>/series/<id>`,
  `/series/<id>` (bare-id shortcut), `/games/<id>`, `/players/<id>`.
- Bot: `handlers/seasons.py`, `handlers/games.py`, rewritten
  `handlers/tournaments.py` (status+type filters, series-aware routing —
  a series-wrapped tournament opens the series screen directly, never the
  plain tournament UI) and matching presenters. "Моё место" card shows
  games played, the top-5 games floor, points, GG, and the two nearest
  rivals.

**Fantasy (increment 4)**
- MS Bot API now passes `tournament_series_id`/`is_practice` through on
  every relevant endpoint (previously silently dropped), plus new
  `/fantasy/events` (browse without knowing a tournament_id),
  `/fantasy/history`, `/fantasy/draft/<id>/cancel`, `/fantasy/draft/<id>`.
- Bot: full rewrite (`handlers/fantasy.py`, `presenters/fantasy.py`) around
  a compact `(tournament_id, series_id, is_practice)` scope encoded in
  callback_data — event picker, draft creation with confirmation, pick/
  unpick, cancel-with-refund confirmation, paid/practice toggle, history
  with pagination.

**Shop, inventory, titles (increment 5)**
- New MS endpoints: `/shop/items`, `/shop/items/<id>`,
  `/shop/items/<id>/buy`, `/inventory`, `/inventory/<id>/equip`,
  `/inventory/<id>/unequip`, `/titles/<id>/equip`, `/titles/unequip`.
- Bot: `handlers/shop.py`, `handlers/inventory.py`, catalog with category
  filters, item card with owned/locked state, buy confirmation + real
  server-side re-check, inventory equip/unequip, title equip/unequip
  wired onto the existing achievements/titles screen.

**Gifts + FSM (increment 6)**
- New MS endpoints: `/gifts/inbox`, `/gifts/history`,
  `/gifts/giftable-items`, `/gifts/send`.
- Bot: `handlers/gifts.py` — minimal FSM (state in `bot/storage.py`, keyed
  by chat_id): pick item -> type recipient nickname -> pick from search
  results -> optional note -> confirm -> send, cancel available at every
  step. Self-gifting and gifting someone else's item are already rejected
  server-side by `GiftService`.

**Notification settings + outbox (increment 7)**
- MS: `NotifyOutboxEvent` model + `NotifyOutboxService` (enqueue/drain with
  exponential backoff, atomic per-row claiming safe under concurrent
  workers) replaces `BotNotifyService`'s old synchronous "POST and hope" —
  same public call sites, now durable. `flask outbox-drain` CLI command
  for cron, optional in-process poller (`OUTBOX_WORKER_ENABLED=true`,
  off by default — every CLI/test invocation also calls `create_app()`).
  Admin observability + manual re-queue at `/admin/analytics/outbox`.
  **Known limitation**: `enqueue()` commits its own short transaction, not
  atomically with the business operation that triggered it — a crash in
  that narrow window could still lose an event. A fully atomic
  transactional outbox is the natural next step if that risk matters more
  than the complexity of threading a shared session through every call
  site.
- Bot: every proactive notification now carries contextual buttons (open
  the game/tournament/Fantasy screen, profile, notification settings),
  respects per-category preferences (`👤 Мой кабинет` → `🔔 Уведомления`),
  and deduplicates by `event_id` (`X-Event-Id` header) so an outbox retry
  can never send a message twice.

**Deep links (increment 8)**
- `bot/deeplink.py` — `/start <payload>` opens a specific screen (game,
  tournament, series evening, Fantasy hub, season table, gifts inbox)
  instead of always the main menu. MS templates (`games/detail.html`,
  `tournaments/detail.html`) now show a "В боте" link generating these
  payloads via a new `telegram_deep_link()` Jinja helper.
- **Not built**: a Telegram Web App. Nothing implemented so far needs one
  — catalogs, tables and Fantasy picks all paginate fine with inline
  buttons — so it's deliberately deferred rather than added speculatively,
  per the spec's own "only where buttons genuinely can't do it" guidance.

**Tests**: every existing test file touched by a signature/behavior change
was updated in place (menu, tournaments, fantasy, ratings/history/economy,
vs, account, notifications) rather than left broken; large batches of new
tests added for the new modules (`storage`, `keyboards/nav`, `dispatch`,
`deeplink`, `ui`, shop/inventory/gifts presenters/handlers). Could not be
executed in the authoring environment (no Python interpreter available) —
see the final session report for exact commands to run and what remains
unverified.

### Added — Полировка: постоянное Reply-меню (последний пункт полировки)

- `bot/presenters/menu.py` (`build_main_menu_markup`) — постоянная
  `ReplyKeyboardMarkup` с кнопками основных разделов: Профиль,
  Статистика, Рейтинг, История, Баланс, Достижения, Турниры, Fantasy,
  Аккаунт.
- `bot/handlers/menu.py` — каждая кнопка (кроме Fantasy/Аккаунт)
  переиспользует уже существующий командный хендлер напрямую
  (`menu_profile` → `handle_me`, `menu_rating` → `handle_rating` и т.д.)
  — новой бизнес-логики не появилось, только текстовый роутинг вместо
  командного. «🎯 Fantasy» — статичная подсказка (Fantasy требует ID
  турнира, который не влезает в кнопку без аргументов). «⚙️ Аккаунт» —
  новая `build_account_status_message` в `presenters/account.py`,
  показывает статус привязки и подсказку `/unlink`.
- `bot/handlers/start.py` — `/start` теперь прикрепляет это меню через
  `reply_markup=build_main_menu_markup()` вместо `None`.
- 14 новых юнит-тестов (было 110, стало 124).
- Проверено кросс-процессно: синтетические `/start` и три кнопки
  (Рейтинг, Аккаунт, Fantasy) через реальный вебхук — Рейтинг и
  Аккаунт реально дёрнули соответствующие эндпоинты MS (видно в её
  логе), Fantasy корректно ответила локальным текстом без похода в API.
- **Вся полировка из "добиваем всё сначала" завершена.** Остался только
  реальный деплой на PythonAnywhere.

### Added — Полировка: инлайн-режим (`@bot Имя`)

- `bot/api_client/endpoints/players.py` (`search_players`) — тонкая
  обёртка над новым `GET /api/v1/bot/players/search?q=` (MS commit
  `b57f00c`, переиспользует существующий `PlayerSearchService`).
- `bot/presenters/players.py` (`build_inline_results`) — по одному
  `InlineQueryResultArticle` на игрока (заголовок/ELO), без похода за
  полной карточкой профиля на кандидата — инлайн-запрос должен успевать
  ответить на каждое нажатие клавиши.
- `bot/handlers/inline.py` (`@bot.inline_handler`) — пустой запрос и
  `ApiError` оба тихо отвечают пустым списком результатов, не падая.
- 5 новых юнит-тестов (было 105, стало 110).
- Проверено кросс-процессно: синтетический `inline_query`-апдейт через
  реальный вебхук → реальный вызов `GET /api/v1/bot/players/search` на
  MS (виден в логе MS, 200, вернул засеянного игрока) → корректно
  собранный `answerInlineQuery` с HTML-текстом карточки; единственная
  ожидаемая ошибка — `401` от настоящего Telegram API (используется
  заведомо фиктивный токен), поймана, HTTP-ответ вебхука всё равно `200`.

### Added — Полировка: остальные 7 fire-and-forget событий

- `bot/presenters/notifications.py` — добавлены
  `build_achievement_granted_message`, `build_title_granted_message`,
  `build_item_bought_out_message`, `build_fantasy_result_message`,
  `build_fantasy_prize_message`, `build_gift_received_message`,
  `build_season_award_message`, `build_game_finished_message`.
- `bot/webhooks/events.py` — `_make_simple_handler(builder)`-фабрика для
  всех 8 типов событий с одним получателем (в отличие от `next-slot`,
  который рассылает списку игроков).
- На стороне MS (commit `a905b21`): `AchievementService.unlock`,
  `TitleService.grant_title`, `ShopService.buyout_item`,
  `GiftService.send_gift`, `FantasyService.score_tournament` (два
  события — результат и приз) и `EconomyService.apply_season_rewards`
  теперь вызывают `BotNotifyService.notify_player(...)` после
  соответствующего бизнес-события.
- Проверено кросс-процессно все 8 типов событий одним прогоном через
  фейковый "event receiver" на :5002 — верные payload и верный
  `telegram_id`-адресат на каждый, включая `season-award`, отдельно
  сработавший для победителя и для не-победителя из top-10 в одном
  вызове `apply_season_rewards`.

### Added — Полировка: команда `/unlink`

- `bot/presenters/account.py` (`build_unlink_confirm_message`,
  `build_unlink_done_message`, `build_unlink_cancelled_message`) —
  Inline-клавиатура Да/Отмена вместо немедленного действия.
- `bot/handlers/account.py` — `handle_unlink` (сообщение) и
  `handle_unlink_callback` (первый `@bot.callback_query_handler` в
  проекте) — реально вызывает `account/unlink`.
- Проверено кросс-процессно синтетическим `callback_query`-апдейтом
  через реальный вебхук.

### Added — Этап 6, инкремент 9: Fantasy (последний крупный раздел меню)

- `bot/api_client/endpoints/fantasy.py`, `presenters/fantasy.py`,
  `handlers/fantasy.py` — `/fantasy <id>`, `/fantasy_create <id>`,
  `/fantasy_available <id>`, `/fantasy_pick <id> <игрок>`,
  `/fantasy_unpick <id> <игрок>`, `/fantasy_leaderboard <id>`.
- **Фикс `ApiClient._request`**: сообщение исключения при 4xx/5xx теперь
  берётся из JSON-поля `message`, а не из сырого текста ответа — бизнес-
  ошибки MS ("уже есть драфт", "нельзя выбрать себя") показываются
  пользователю читаемым текстом, а не куском JSON. `tests/test_api_client.py`
  (6 тестов) покрывает разворачивание конверта и все типы исключений.
- 77 юнит-тестов (было 54, +23). Проверено кросс-процессно против
  реального MS: полный жизненный цикл драфта, включая повторное создание
  (корректно отклонено с читаемым сообщением) и сужение доступных
  игроков после пика.
- **Все разделы меню из согласованного функционала реализованы.**

### Added — Этап 6, инкремент 8: турниры (только просмотр)

- `bot/api_client/endpoints/tournaments.py`, `presenters/tournaments.py`,
  `handlers/tournaments.py` — `/tournaments [pending|active|finished]`,
  `/tournament <id>`. Без привязки аккаунта (публичные данные).
- 54 юнит-теста (было 45, +9). Проверено кросс-процессно против
  реального MS: список показывает засеянный турнир, детали — верное
  название активной стадии и винрейты игроков.

### Added — Этап 6, инкремент 7: рейтинг/история/экономика/достижения/титулы

- `bot/api_client/endpoints/{ratings,history,economy,achievements}.py` —
  тонкие обёртки над второй партией MS-эндпоинтов.
- `bot/presenters/{ratings,history,economy,achievements}.py` — чистые
  функции форматирования.
- `bot/handlers/{ratings,history,economy,achievements}.py` — команды
  `/rating [страница]`, `/history [страница]`, `/balance` (баланс +
  последние 5 операций одним сообщением), `/achievements`,
  `/pin <id>`/`/unpin <id>`, `/titles`.
- 45 юнит-тестов (было 30, +15 новых).
- Проверено кросс-процессно против реального MS: все семь новых
  эндпоинтов, включая pin→unpin, реально переключающий флаг на сервере.

### Added — Этап 6, инкремент 6: бот подключён к /api/v1/bot/*

- `bot/api_client/client.py` — разворачивает конверт MS
  `{status,message,data}`, `ApiError` при `status != "ok"`.
- `bot/api_client/endpoints/profile.py` (`resolve`/`get_profile`/
  `get_stats`/`compare`), `endpoints/account.py` (`unlink`) — тонкие
  типизированные обёртки, без логики.
- `bot/services/linking_service.py` — общее правило "не привязан —
  предложи привязать" для всех хендлеров, которым нужен конкретный игрок.
- `bot/presenters/profile.py` (`build_not_linked_message`,
  `build_welcome_back_message`, `build_profile_card`),
  `presenters/stats.py`, `presenters/compare.py` — чистые функции.
- `bot/handlers/start.py` (переписан) — `/start` реально резолвит
  вызывающего. Новые `handlers/profile.py` (`/me`, `/stats`),
  `handlers/compare.py` (`/compare <id>`). Каждый хендлер ловит `ApiError`
  и отвечает дружелюбным текстом.
- Удалён устаревший `presenters/start.py` (статичное сообщение "бот в
  разработке" — больше не нужно, есть реальные данные).
- 30 юнит-тестов (было 13): пресентеры — чистые функции; хендлеры —
  с моками `resolve`/API-вызовов/`send_message`.
- Проверено кросс-процессно: реальный бот-процесс на :5001 вызывает
  реальный MS-процесс на :5000 через `ApiClient` — resolve, profile,
  stats, compare, unlink дали корректный, осмысленный текст.

### Зависимость закрыта (изменение на стороне MS, не в этом репозитории)

- Первая партия `/api/v1/bot/*` реализована на MS (`resolve`, `profile`,
  `stats`, `compare`, `account/unlink`, commit `e6af578`) — авторизация
  серверным bearer-токеном, версионировано. Теперь полностью подключена
  к боту (см. "Added" выше).

### Added — Этап 6, инкремент 4: обработка next-slot событий

- `bot/webhooks/events.py` — `dispatch(event_type, payload)`, реестр
  `EVENT_HANDLERS` (расширяемый под будущие типы событий),
  `handle_next_slot` шлёт сообщение через `TeleBot.send_message` каждому
  игроку из payload'а, сбой отправки одному не прерывает рассылку
  остальным (например, игрок ни разу не нажимал `/start` — Telegram не
  даст написать первым).
- `bot/presenters/notifications.py` — `build_next_slot_message` (чистая
  функция, без сети).
- `bot/__init__.py` — `/events/<type>` теперь реально вызывает `dispatch`
  вместо всегда-501; сбой обработки ловится и возвращает 200 (сайт,
  приславший событие, не должен ничего "чинить" из-за временной проблемы
  у бота).
- `tests/conftest.py` (новый) — фейковые обязательные env-переменные:
  это первый тестовый файл, которому реально нужен импорт
  `bot.telegram_bot` (чтобы замокать `send_message`), а не только чистые
  presenters/security. 13 тестов проходят.
- Проверено между двумя реально запущенными серверами (MS локально шлёт
  настоящий подписанный HTTP-запрос на локально запущенный бот) —
  корректная подпись, корректный payload, реальная попытка отправки в
  Telegram видна в логе (падает только из-за тестового токена).

### Зависимости закрыты (изменения на стороне MS, не в этом репозитории)

- `Player.telegram_id` + Telegram Login Widget реализованы на основном
  сайте (MS, commit `98e6db1`) — кнопка привязки в профиле, HMAC-проверка
  подписи виджета, роуты `/auth/telegram/callback`/`/auth/telegram/unlink`.
  Для бота это означает: как только на MS появится
  `GET /api/v1/bot/resolve?telegram_id=`, `/start` сможет реально
  резолвить пользователя вместо статичного приветствия.
- Авторассадка следующего раунда турнира реализована на MS
  (`Game.round_number`, `TournamentService.generate_next_round`, commit
  `ea0fe90`) — минимизация повторных мест/составов, честная ротация
  отдыха. `finish_game` на MS теперь реально шлёт событие `next-slot`
  боту (commit `4d081fd`) — обработка этого события на стороне бота
  описана в разделе "Added" выше.

### Added — Этап 6, инкремент 1: каркас проекта

- Структура каталогов (`bot/handlers`, `presenters`, `services`,
  `api_client`, `webhooks`).
- `bot/config.py` — конфигурация из env, обязательные переменные без
  тихого fallback (тот же принцип, что `DATABASE_URL` в основном
  проекте).
- `bot/security.py` — проверка секрета вебхука Telegram
  (`X-Telegram-Bot-Api-Secret-Token`) и HMAC-подписи входящих событий
  от основного сайта (`X-Signature`). Покрыто юнит-тестами.
- `bot/api_client/` — базовый `ApiClient` (сессия с ретраями на
  сетевые/5xx-ошибки, таймауты, типизированные исключения
  `ApiTimeout`/`ApiUnauthorized`/`ApiNotFound`/`ApiServerError`).
  Конкретные эндпоинты появятся вместе с фичами, которые их используют.
- `bot/telegram_bot.py` — синглтоны `TeleBot` (синхронный режим,
  `threaded=False`) и `ApiClient`.
- Flask app factory (`bot/__init__.py`) — тот же паттерн, что
  `app/__init__.py` основного проекта (конфиг импортируется внутри
  `create_app()`, не на уровне модуля — иначе любой импорт `bot.*`
  требовал бы реальных секретов).
  - `GET /health` — liveness-проверка.
  - `POST /telegram/webhook/<путь-токен>` — приём апдейтов от Telegram,
    двойная защита (секретный путь + secret_token в заголовке).
    Ошибки внутри хендлеров логируются, но не валят HTTP-ответ 500-й —
    Telegram всегда получает 200, иначе будет ретраить апдейт.
  - `POST /events/<type>` — приём уведомлений от основного сайта,
    HMAC-подпись обязательна. Обработка конкретных типов событий —
    в следующих инкрементах (сейчас 501).
- Первый рабочий вертикальный срез: `/start` → `handlers/start.py` →
  `presenters/start.py` (приветственное сообщение, честно объясняет,
  что привязка аккаунта ещё не готова) → отправка через `TeleBot`.
- Юнит-тесты (`tests/test_security.py`, `tests/test_presenters_start.py`)
  — 7 тестов, все проходят, без сети и без реального токена бота.
- `requirements.txt`, `.env.example`, `.gitignore`, `deploy.sh`
  (тот же паттерн git-pull+touch-WSGI, что у основного проекта),
  `run.py`.

### Проверено вручную

- Локальный запуск с фейковыми env-значениями: `/health` → 200,
  вебхук без секрета/с неверным секретом/с неверным путём → 403/403/404,
  синтетический Update с `/start` → полный конвейер (подпись → парсинг →
  диспетчеризация → пресентер → попытка отправки) отработал корректно;
  единственная ожидаемая ошибка — `401` от настоящего Telegram API
  (используется заведомо фиктивный токен), корректно залогирована,
  HTTP-ответ всё равно `200`.

### Известные ограничения на этой стадии

- Бот пока не умеет ничего, кроме `/start` — остальной функционал
  (профиль, статистика, рейтинг, турниры, Fantasy, уведомления) требует
  сначала соответствующих изменений в основном проекте (`Player.telegram_id`,
  Login Widget, `/api/v1/bot/*`, `Game.round_number`, авторассадка,
  события) — см. ARCHITECTURE.md, раздел "Зависимости от основного проекта".
- `MAIN_API_SERVICE_TOKEN`/`INCOMING_EVENT_SECRET` — секреты для связи с
  основным сайтом, реальные значения появятся, когда там будет готова
  соответствующая часть API.

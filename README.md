# 🤖 MafiaStyle Telegram Bot

Официальный Telegram-клиент для [MafiaTracker](../MS) — полностью отдельное
приложение: свой репозиторий, свой аккаунт PythonAnywhere, своя (минимальная
или отсутствующая) база данных. Никакого прямого доступа к БД основного
сайта — всё взаимодействие только через его API.

Подробности архитектуры, принятых решений и их причин — см.
[ARCHITECTURE.md](ARCHITECTURE.md).

## Стек

- Python 3.11+, Flask (вебхук-модель, без фонового процесса/поллинга)
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (`telebot`) — синхронная библиотека, естественно ложится на вебхук-модель WSGI-хостинга (PythonAnywhere)
- `requests` — HTTP-клиент к API основного сайта

## Быстрый старт (локально)

```bash
python -m venv .venv
./.venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # заполнить реальными значениями
python -m pytest tests/    # юнит-тесты (security + presenters — без сети)
python run.py               # локальный dev-сервер на :5000
```

## Структура проекта

```
bot/
  config.py          # конфигурация из переменных окружения
  telegram_bot.py     # синглтоны TeleBot и ApiClient
  handlers/            # Telegram-хендлеры (тонкие — парсинг апдейта → services → presenters → отправка)
    group_commands.py    # публичные команды общего чата: /top, /season, /player, /game, /help
  presenters/          # чистые функции: данные → (текст, клавиатура), без сети
    group.py             # компактные экраны для группового чата (без пагинации, без callback на private_only)
  services/            # бизнес-правила бота (склейка handlers ↔ api_client)
  api_client/          # единственное место HTTP-вызовов к основному сайту
  webhooks/            # обработка входящих событий ОТ основного сайта
  keyboards/nav.py      # версионированный callback_data, Назад/Домой, пагинация
  dispatch.py           # guarded_callback — общий wrapper колбэков (double-tap, гарантированный answer, private_only)
  chat_policy.py         # private-vs-group политика: is_private/is_group, require_private_message
  i18n.py                # единый слой русской локализации/форматирования (статусы, монеты, баллы, даты, склонения)
  commands.py            # setMyCommands по scope (личные/групповые команды), см. `flask set-commands`
  bot_identity.py        # @username бота, deep-link URL в личный чат из группового экрана
  storage.py            # локальный SQLite: FSM (chat_id, telegram_user_id), дедуп событий, настройки уведомлений
  deeplink.py            # /start <payload> → конкретный экран
  ui.py                  # esc()/форматирование — общая "дизайн-система" пресентеров
  security.py          # проверка подписи вебхука Telegram и HMAC входящих событий
tests/                  # юнит-тесты (пресентеры/security — без сети и без реального токена)
```

Подробности новой архитектуры (навигация, `storage.py`, outbox, deep
links) — см. [ARCHITECTURE.md](ARCHITECTURE.md).

## Переменные окружения

См. [.env.example](.env.example) — все обязательны, приложение не
запустится без них (тот же принцип, что `DATABASE_URL` в основном
проекте — без тихого fallback).

## Деплой

На отдельном аккаунте PythonAnywhere: `git pull` + `bash deploy.sh`
(тот же паттерн, что у основного проекта). Не забудьте прописать
реальный путь к WSGI-файлу в `deploy.sh` под ваш аккаунт.

## Статус

🚧 В разработке. Текущий этап и история изменений — см. [CHANGELOG.md](CHANGELOG.md).

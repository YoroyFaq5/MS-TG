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
  presenters/          # чистые функции: данные → (текст, клавиатура), без сети
  services/            # бизнес-правила бота (склейка handlers ↔ api_client)
  api_client/          # единственное место HTTP-вызовов к основному сайту
  webhooks/            # обработка входящих событий ОТ основного сайта
  security.py          # проверка подписи вебхука Telegram и HMAC входящих событий
tests/                  # юнит-тесты (пресентеры/security — без сети и без реального токена)
```

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

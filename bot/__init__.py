"""
Flask app factory — тот же паттерн, что и app/__init__.py::create_app()
основного проекта. Приложение синхронное, вебхук-модель: каждый апдейт от
Telegram — обычный HTTP POST-запрос, обрабатывается и отвечает в рамках
одного WSGI-запроса, без фонового процесса.

Импорт config_map — ВНУТРИ create_app(), не на уровне модуля: иначе
любой импорт bot.* (в т.ч. из тестов, которым не нужен реальный токен)
тянет за собой обязательную проверку env-переменных Config (см.
bot/config.py) просто за счёт того, что Python исполняет __init__.py
пакета при импорте любого его подмодуля — та же ловушка, что уже была
учтена в app/__init__.py основного проекта.
"""


def create_app(config_name: str = "default"):
    import logging

    import telebot
    from flask import Flask, abort, jsonify, request

    from bot.config import config_map
    from bot.logging_config import setup_logging
    from bot.security import verify_event_signature, verify_telegram_secret

    logger = logging.getLogger(__name__)
    app = Flask(__name__)
    cfg = config_map[config_name]
    app.config.from_object(cfg)

    setup_logging(debug=cfg.DEBUG)

    # bot.telegram_bot читает Config при импорте (создаёт TeleBot/
    # ApiClient); bot.handlers регистрирует все @bot.message_handler
    # декораторы — оба импорта нарочно отложены до сюда же.
    from bot.telegram_bot import bot as telegram_bot
    import bot.handlers  # noqa: F401

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post(f"/telegram/webhook/{cfg.TELEGRAM_WEBHOOK_PATH_TOKEN}")
    def telegram_webhook():
        received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not verify_telegram_secret(received_secret, cfg.TELEGRAM_WEBHOOK_SECRET):
            abort(403)
        update = telebot.types.Update.de_json(request.get_json(force=True))
        try:
            telegram_bot.process_new_updates([update])
        except Exception:
            # Ошибка внутри хендлера (в т.ч. сбой самого Telegram API при
            # отправке ответа) не должна валить весь HTTP-ответ Telegram'у
            # 500-й — иначе Telegram будет ретраить один и тот же апдейт.
            # Возвращаем 200 в любом случае, ошибку логируем для разбора.
            logger.exception("Ошибка обработки Telegram-апдейта")
        return jsonify(ok=True)

    @app.post("/events/<event_type>")
    def incoming_event(event_type: str):
        signature = request.headers.get("X-Signature")
        if not verify_event_signature(request.get_data(), signature, cfg.INCOMING_EVENT_SECRET):
            abort(403)
        # Обработка конкретных типов событий (game-finished, next-slot,
        # achievement-granted, ...) добавляется по мере готовности
        # соответствующих фич на стороне основного сайта.
        return jsonify(ok=True, event_type=event_type, handled=False), 501

    return app

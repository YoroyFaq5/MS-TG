"""
Тестовые заглушки обязательных переменных окружения (см. bot/config.py) —
нужны, потому что часть тестов (webhooks/events) реально импортирует
bot.telegram_bot (создаёт TeleBot с этим токеном), а не только чистые
presenters. Заведомо фиктивные значения — сеть в тестах не дёргается,
send_message всегда мокается.
"""
import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:TEST-FAKE-TOKEN")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("TELEGRAM_WEBHOOK_PATH_TOKEN", "test-path-token")
os.environ.setdefault("MAIN_API_BASE_URL", "http://localhost:9999")
os.environ.setdefault("MAIN_API_SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("INCOMING_EVENT_SECRET", "test-event-secret")

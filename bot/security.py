"""
Проверка подлинности двух РАЗНЫХ входящих направлений — не путать:

1. Telegram -> бот: секретный путь вебхука + заголовок X-Telegram-Bot-Api-
   Secret-Token, который Telegram сам присылает при каждом вызове, если он
   был задан при регистрации вебхука (setWebhook(secret_token=...)).
2. Основной сайт -> бот (fire-and-forget уведомления о событиях): общий
   HMAC-секрет, которого не знает никто, кроме этих двух серверов.

Обе проверки — чистые функции, без сети и без Flask-контекста, чтобы их
было легко покрыть юнит-тестами.
"""
import hashlib
import hmac


def verify_telegram_secret(received_secret: str | None, expected_secret: str) -> bool:
    if not received_secret:
        return False
    return hmac.compare_digest(received_secret, expected_secret)


def verify_event_signature(payload: bytes, received_signature: str | None, secret: str) -> bool:
    """
    received_signature — hex-строка HMAC-SHA256(payload, secret), которую
    основной сайт кладёт в заголовок X-Signature при отправке события.
    """
    if not received_signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received_signature, expected)

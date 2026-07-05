from bot.security import verify_event_signature, verify_telegram_secret


def test_verify_telegram_secret_matches():
    assert verify_telegram_secret("abc123", "abc123") is True


def test_verify_telegram_secret_mismatch():
    assert verify_telegram_secret("wrong", "abc123") is False


def test_verify_telegram_secret_missing():
    assert verify_telegram_secret(None, "abc123") is False


def test_verify_event_signature_matches():
    import hashlib
    import hmac

    secret = "shared-secret"
    payload = b'{"foo": "bar"}'
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_event_signature(payload, signature, secret) is True


def test_verify_event_signature_mismatch():
    assert verify_event_signature(b"payload", "deadbeef", "secret") is False


def test_verify_event_signature_missing():
    assert verify_event_signature(b"payload", None, "secret") is False

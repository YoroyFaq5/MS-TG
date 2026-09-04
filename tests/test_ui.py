from bot.ui import esc, truncate, fmt_money, fmt_signed, fmt_date, empty_state, error_state, stale_state


def test_esc_escapes_html_special_chars():
    assert esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert esc("Tom & Jerry") == "Tom &amp; Jerry"


def test_esc_handles_none_and_non_string():
    assert esc(None) == ""
    assert esc(42) == "42"


def test_esc_does_not_escape_quotes_by_default():
    """quote=False — Telegram's HTML parse mode doesn't need attribute-safe
    quoting, only the entity-breaking chars matter here."""
    assert esc('He said "hi"') == 'He said "hi"'


def test_truncate_short_text_unchanged():
    assert truncate("short", 20) == "short"


def test_truncate_long_text_gets_ellipsis():
    result = truncate("a" * 30, 10)
    assert len(result) == 10
    assert result.endswith("…")


def test_fmt_money():
    assert fmt_money(1234) == "1 234"
    assert fmt_money(0) == "0"
    assert fmt_money("not a number") == "0"


def test_fmt_signed():
    assert fmt_signed(5) == "+5.0"
    assert fmt_signed(-5) == "-5.0"
    assert fmt_signed(0) == "+0.0"


def test_fmt_date_handles_none():
    assert fmt_date(None) == "—"


def test_fmt_date_truncates_to_10_chars():
    assert fmt_date("2026-06-21T12:00:00+00:00") == "2026-06-21"


def test_state_helpers_escape_their_text():
    assert "<b>" not in empty_state("<b>x</b>")
    assert "<b>" not in error_state("<b>x</b>")
    assert "<b>" not in stale_state("<b>x</b>")

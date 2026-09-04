from bot.keyboards.nav import (
    cb, parse_cb, is_cb, home_button, back_button, nav_row, add_nav_footer,
    pagination_row, confirm_row, NOOP, CALLBACK_MAX_BYTES,
)


def test_cb_builds_versioned_string():
    assert cb("shop", "item", 42) == "v1:shop:item:42"


def test_parse_cb_strips_version_prefix():
    assert parse_cb("v1:shop:item:42") == ["shop", "item", "42"]


def test_parse_cb_handles_unversioned_legacy_data():
    assert parse_cb("legacy:1") == ["legacy", "1"]


def test_is_cb_matches_domain_and_action():
    assert is_cb("v1:shop:item:42", "shop", "item") is True
    assert is_cb("v1:shop:item:42", "shop", "list") is False
    assert is_cb("v1:shop:item:42", "inv") is False


def test_is_cb_domain_only_ignores_action():
    assert is_cb("v1:shop:item:42", "shop") is True


def test_cb_never_exceeds_telegram_limit_for_realistic_ids():
    # Even with a large 64-bit-ish id and a few extra numeric args, the
    # encoded string must stay well under Telegram's 64-byte ceiling —
    # spec: "Callback data должна быть версионированной, короткой и
    # укладываться в лимит Telegram 64 байта."
    data = cb("fantasy", "pickf", 999999999, 999999999, 1, 999999999)
    assert len(data.encode("utf-8")) <= CALLBACK_MAX_BYTES


def test_cb_never_contains_business_data_only_ids_and_actions():
    """Nothing produced by cb() should ever look like a price/permission —
    it's a pure structural check: every part must be a short token or an
    integer, never a free-form string that could carry business data."""
    data = cb("shop", "buy", 42, "profile_customization")
    parts = parse_cb(data)
    for part in parts[2:]:
        assert part.isdigit() or part.replace("_", "").isalnum()


def test_home_button_targets_nav_home():
    assert home_button().callback_data == cb("nav", "home")


def test_back_button_uses_given_target():
    btn = back_button("v1:tourn:list:-:1", label="← Турниры")
    assert btn.callback_data == "v1:tourn:list:-:1"
    assert btn.text == "← Турниры"


def test_nav_row_omits_back_when_not_given():
    row = nav_row(back_target=None)
    assert len(row) == 1
    assert row[0].callback_data == cb("nav", "home")


def test_nav_row_includes_back_when_given():
    row = nav_row(back_target="v1:x:y")
    assert len(row) == 2


def test_add_nav_footer_creates_markup_when_none_given():
    markup = add_nav_footer(None)
    assert markup is not None
    buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("nav", "home") for b in buttons)


def test_pagination_row_first_page_has_no_previous():
    row = pagination_row("v1:x:list", 1, 5)
    labels = [b.text for b in row]
    assert not any(l.startswith("◀") for l in labels)
    assert any(l.startswith("▶") for l in labels)
    assert any("1/5" in l for l in labels)


def test_pagination_row_middle_page_has_both():
    row = pagination_row("v1:x:list", 3, 5)
    labels = [b.text for b in row]
    assert any(l.startswith("◀") for l in labels)
    assert any(l.startswith("▶") for l in labels)


def test_pagination_row_last_page_has_no_next():
    row = pagination_row("v1:x:list", 5, 5)
    labels = [b.text for b in row]
    assert any(l.startswith("◀") for l in labels)
    assert not any(l.startswith("▶") for l in labels)


def test_pagination_row_single_page_has_neither_but_shows_indicator():
    row = pagination_row("v1:x:list", 1, 1)
    labels = [b.text for b in row]
    assert not any(l.startswith("◀") for l in labels)
    assert not any(l.startswith("▶") for l in labels)
    assert "1/1" in labels[0]


def test_pagination_row_callback_data_targets_correct_pages():
    row = pagination_row("v1:x:list", 3, 5, extra_parts=("active",))
    prev_btn = next(b for b in row if b.text.startswith("◀"))
    next_btn = next(b for b in row if b.text.startswith("▶"))
    assert prev_btn.callback_data == "v1:x:list:2:active"
    assert next_btn.callback_data == "v1:x:list:4:active"


def test_noop_button_is_a_stable_sentinel():
    assert NOOP == "v1:noop"


def test_confirm_row_has_two_distinct_targets():
    row = confirm_row("v1:a:yes", "v1:a:no")
    assert row[0].callback_data == "v1:a:yes"
    assert row[1].callback_data == "v1:a:no"

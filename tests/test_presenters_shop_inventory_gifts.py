from bot.presenters.shop import (
    build_shop_hub_message, build_shop_list_message, build_shop_item_message,
    build_buy_confirm_message, build_buy_result_message,
)
from bot.presenters.inventory import build_inventory_hub_message, build_inventory_list_message
from bot.presenters.gifts import (
    build_gifts_hub_message, build_inbox_message, build_pick_item_message,
    build_ask_recipient_message, build_recipient_results_message, build_confirm_message,
)
from bot.keyboards.nav import cb


def _paged(items, page=1, total_pages=1):
    return {"items": items, "page": page, "per_page": 8, "total": len(items), "total_pages": total_pages}


def test_shop_hub_lists_all_categories():
    _, markup = build_shop_hub_message()
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("shop", "list", "-", 1) in all_cb
    assert cb("shop", "list", "nickname", 1) in all_cb


def test_shop_list_message_shows_owned_and_locked_marks():
    data = _paged([
        {"id": 1, "name": "Frame", "price": 100.0, "already_owned": True, "current_owner_id": None},
        {"id": 2, "name": "Golden Crown", "price": 500.0, "already_owned": False, "current_owner_id": 9},
    ])
    text, _ = build_shop_list_message(data, None)
    assert "✅" in text
    assert "🔒" in text


def test_shop_list_message_escapes_item_name():
    data = _paged([{"id": 1, "name": "<b>Evil</b>", "price": 1.0, "already_owned": False, "current_owner_id": None}])
    text, _ = build_shop_list_message(data, None)
    assert "<b>Evil</b>" not in text
    assert "&lt;b&gt;" in text


def test_shop_item_message_hides_buy_button_when_already_owned():
    item = {
        "id": 1, "name": "Frame", "price": 10.0, "rarity": "common", "description": None,
        "category": "profile_customization", "already_owned": True, "current_owner_id": None,
        "is_active": True, "balance": 50.0,
    }
    _, markup = build_shop_item_message(item, None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert not any(c.startswith(cb("shop", "buy-confirm")) for c in all_cb)


def test_shop_item_message_shows_buy_button_when_purchasable():
    item = {
        "id": 1, "name": "Frame", "price": 10.0, "rarity": "common", "description": None,
        "category": "profile_customization", "already_owned": False, "current_owner_id": None,
        "is_active": True, "balance": 50.0,
    }
    _, markup = build_shop_item_message(item, None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("shop", "buy-confirm", 1, "-") in all_cb


def test_buy_confirm_requires_explicit_confirmation():
    item = {"id": 1, "name": "Frame", "price": 10.0}
    text, markup = build_buy_confirm_message(item, None)
    assert "Купить" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("shop", "buy", 1, "-") in all_cb
    assert cb("shop", "item", 1, "-") in all_cb  # cancel goes back to item, not straight to buy


def test_buy_result_links_to_inventory():
    item = {"id": 1, "name": "Frame", "price": 10.0}
    text, markup = build_buy_result_message("«Frame» куплен.", item, None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("inv", "list", "-") in all_cb


def test_inventory_hub_lists_categories():
    _, markup = build_inventory_hub_message()
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("inv", "list", "-") in all_cb


def test_inventory_list_shows_equip_and_gift_actions():
    items = [{
        "id": 5,
        "item": {
            "id": 1, "name": "Frame", "rarity": "common", "category": "profile_customization",
            "is_transferable": True,
        },
        "is_equipped": False,
    }]
    text, markup = build_inventory_list_message(items, None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("inv", "equip", 5, "-") in all_cb
    assert cb("gift", "send-pick", 5) in all_cb


def test_inventory_list_equipped_item_offers_unequip_not_gift():
    items = [{
        "id": 5,
        "item": {
            "id": 1, "name": "Frame", "rarity": "common", "category": "profile_customization",
            "is_transferable": True,
        },
        "is_equipped": True,
    }]
    text, markup = build_inventory_list_message(items, None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("inv", "unequip", 5, "-") in all_cb
    assert cb("gift", "send-pick", 5) not in all_cb  # can't gift an equipped item (site rule)


def test_inventory_list_physical_item_has_no_equip_action():
    items = [{
        "id": 5,
        "item": {"id": 1, "name": "T-shirt", "rarity": "common", "category": "physical", "is_transferable": False},
        "is_equipped": False,
    }]
    _, markup = build_inventory_list_message(items, None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("inv", "equip", 5, "-") not in all_cb
    assert cb("gift", "send-pick", 5) not in all_cb  # not transferable either


def test_gifts_hub_has_three_sections():
    _, markup = build_gifts_hub_message()
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("gift", "inbox", 1) in all_cb
    assert cb("gift", "send") in all_cb
    assert cb("gift", "history", 1) in all_cb


def test_inbox_message_marks_unseen():
    data = _paged([{
        "from_player_name": "Bob", "shop_item": {"name": "Frame"}, "seen": False, "message": None,
    }])
    text, _ = build_inbox_message(data)
    assert "🆕" in text


def test_inbox_message_escapes_note():
    data = _paged([{
        "from_player_name": "Bob", "shop_item": {"name": "Frame"}, "seen": True, "message": "<i>hi</i>",
    }])
    text, _ = build_inbox_message(data)
    assert "<i>hi</i>" not in text
    assert "&lt;i&gt;" in text


def test_pick_item_message_empty_explains_why():
    text, _ = build_pick_item_message([])
    assert "Нечего дарить" in text


def test_ask_recipient_message_has_cancel():
    text, markup = build_ask_recipient_message()
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("gift", "cancel") in all_cb


def test_recipient_results_excludes_nothing_but_shows_query():
    text, markup = build_recipient_results_message(
        [{"id": 2, "display_name": "Rival", "elo": 1000}], "riv",
    )
    assert "riv" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("gift", "recip", 2) in all_cb
    assert cb("gift", "cancel") in all_cb


def test_confirm_message_shows_item_recipient_and_note():
    text, markup = build_confirm_message("Frame", "Rival", "gg wp")
    assert "Frame" in text and "Rival" in text and "gg wp" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("gift", "confirm") in all_cb
    assert cb("gift", "cancel") in all_cb


def test_confirm_message_escapes_note():
    text, _ = build_confirm_message("Frame", "Rival", "<script>x</script>")
    assert "<script>" not in text

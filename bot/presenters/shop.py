from typing import Optional, Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc, fmt_money, truncate

CATEGORY_LABELS = {
    "profile_customization": "🎨 Оформление профиля",
    "nickname": "🏷 Ник",
    "physical": "📦 Физические призы",
}
RARITY_LABELS = {
    "common": "Обычный", "rare": "Редкий", "epic": "Эпический",
    "legendary": "Легендарный", "mythic": "Мифический", "ultra": "Ультра",
}


def build_shop_hub_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🛍 <b>Магазин</b>\n\nВыбери категорию:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗂 Все товары", callback_data=cb("shop", "list", "-", 1)))
    for key, label in CATEGORY_LABELS.items():
        markup.add(types.InlineKeyboardButton(label, callback_data=cb("shop", "list", key, 1)))
    return text, add_nav_footer(markup)


def build_shop_list_message(data: dict, category: Optional[str]) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    label = CATEGORY_LABELS.get(category, "Все товары")
    lines = [f"🛍 <b>{label}</b> — стр. {page}/{total_pages}", ""]
    markup = types.InlineKeyboardMarkup()
    for item in items:
        owned_mark = " ✅" if item["already_owned"] else ""
        locked_mark = " 🔒" if item.get("current_owner_id") else ""
        lines.append(f"{esc(item['name'])} — {fmt_money(item['price'])}₽{owned_mark}{locked_mark}")
        markup.add(types.InlineKeyboardButton(
            f"{truncate(item['name'], 36)} · {fmt_money(item['price'])}",
            callback_data=cb("shop", "item", item["id"], category or "-"),
        ))
    if not items:
        lines.append("Пусто.")
    if items:
        markup.row(*pagination_row(cb("shop", "list", category or "-"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("shop", "hub"))


def build_shop_item_message(item: dict, category: Optional[str]) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [
        f"🛍 <b>{esc(item['name'])}</b>",
        f"Редкость: {RARITY_LABELS.get(item['rarity'], item['rarity'])} · Цена: {fmt_money(item['price'])}",
    ]
    if item.get("description"):
        lines.append(f"\n{esc(item['description'])}")
    if item["category"] == "physical":
        lines.append("\n📦 Физический приз — выдаётся администратором вручную после покупки.")
    if item.get("current_owner_id"):
        lines.append("\n🔒 Уникальный предмет — уже принадлежит другому игроку. Перекуп доступен только на сайте.")
    if item["already_owned"]:
        lines.append("\n✅ Уже у вас в инвентаре.")
    if item.get("balance") is not None:
        lines.append(f"\nВаш баланс: {fmt_money(item['balance'])}")

    markup = types.InlineKeyboardMarkup()
    can_buy = not item["already_owned"] and not item.get("current_owner_id") and item["is_active"]
    if can_buy:
        markup.row(types.InlineKeyboardButton(
            f"💳 Купить за {fmt_money(item['price'])}",
            callback_data=cb("shop", "buy-confirm", item["id"], category or "-"),
        ))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("shop", "list", category or "-", 1))


def build_buy_confirm_message(item: dict, category: Optional[str]) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = (
        f"💳 Купить «{esc(item['name'])}» за <b>{fmt_money(item['price'])}</b> монет?\n"
        f"Баланс спишется сразу, отменить покупку после подтверждения будет нельзя."
    )
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Купить", callback_data=cb("shop", "buy", item["id"], category or "-")),
        types.InlineKeyboardButton("✖️ Отмена", callback_data=cb("shop", "item", item["id"], category or "-")),
    )
    return text, markup


def build_buy_result_message(result_message: str, item: dict, category: Optional[str]) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = f"✅ {esc(result_message)}"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🎒 Инвентарь", callback_data=cb("inv", "list", "-")))
    return text, add_nav_footer(markup, back_target=cb("shop", "list", category or "-", 1))

from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc, truncate
from bot.presenters.shop import CATEGORY_LABELS


def build_inventory_hub_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🎒 <b>Инвентарь</b>\n\nВыбери категорию:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗂 Всё", callback_data=cb("inv", "list", "-")))
    for key, label in CATEGORY_LABELS.items():
        markup.add(types.InlineKeyboardButton(label, callback_data=cb("inv", "list", key)))
    return text, add_nav_footer(markup)


def build_inventory_list_message(items: list, category) -> Tuple[str, types.InlineKeyboardMarkup]:
    label = CATEGORY_LABELS.get(category, "Всё")
    lines = [f"🎒 <b>Инвентарь — {label}</b>", ""]
    markup = types.InlineKeyboardMarkup()
    for inv in items:
        item = inv["item"]
        equipped_mark = " ✅ экипировано" if inv["is_equipped"] else ""
        lines.append(f"{esc(item['name'])} ({i18n.tr('rarity', item['rarity'])}){equipped_mark}")
        if item["category"] != "physical":
            action = "unequip" if inv["is_equipped"] else "equip"
            action_label = "📤 Снять" if inv["is_equipped"] else "🎽 Экипировать"
            markup.add(types.InlineKeyboardButton(
                f"{action_label}: {truncate(item['name'], 30)}",
                callback_data=cb("inv", action, inv["id"], category or "-"),
            ))
        if item["is_transferable"] and not inv["is_equipped"]:
            markup.add(types.InlineKeyboardButton(
                f"🎁 Подарить: {truncate(item['name'], 26)}",
                callback_data=cb("gift", "send-pick", inv["id"]),
            ))
    if not items:
        lines.append("Пусто — загляни в магазин.")
        markup.add(types.InlineKeyboardButton("🛍 В магазин", callback_data=cb("shop", "hub")))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("inv", "hub"))

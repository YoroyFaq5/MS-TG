from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc, truncate


def build_gifts_hub_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🎁 <b>Подарки</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📥 Входящие", callback_data=cb("gift", "inbox", 1)))
    markup.row(types.InlineKeyboardButton("📤 Отправить подарок", callback_data=cb("gift", "send")))
    markup.row(types.InlineKeyboardButton("📜 История", callback_data=cb("gift", "history", 1)))
    return text, add_nav_footer(markup)


def build_inbox_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page, total_pages = data["page"], data["total_pages"] or 1
    lines = [f"📥 <b>Входящие подарки</b> — {i18n.page_indicator(page, total_pages)}", ""]
    for t in items:
        seen_mark = "" if t["seen"] else " 🆕"
        item_name = t["shop_item"]["name"] if t.get("shop_item") else "?"
        lines.append(f"{esc(t['from_player_name'])} → «{esc(item_name)}»{seen_mark}")
        if t.get("message"):
            lines.append(f"  «{esc(t['message'])}»")
    if not items:
        lines.append("Пока пусто.")
    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("gift", "inbox"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_history_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page, total_pages = data["page"], data["total_pages"] or 1
    lines = [f"📜 <b>История подарков</b> — {i18n.page_indicator(page, total_pages)}", ""]
    for t in items:
        item_name = t["shop_item"]["name"] if t.get("shop_item") else "?"
        lines.append(f"{esc(t['from_player_name'])} → {esc(t['to_player_name'])}: «{esc(item_name)}»")
    if not items:
        lines.append("Пока пусто.")
    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("gift", "history"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_pick_item_message(items: list) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "📤 <b>Отправить подарок</b>\n\nВыбери предмет из инвентаря:"
    markup = types.InlineKeyboardMarkup()
    for inv in items:
        item = inv["item"]
        markup.add(types.InlineKeyboardButton(
            truncate(item["name"], 40), callback_data=cb("gift", "send-pick", inv["id"]),
        ))
    if not items:
        text += "\n\nНечего дарить — все предметы либо неотчуждаемые, либо экипированы."
    return text, add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_ask_recipient_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "👤 Напиши ник получателя одним сообщением."
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✖️ Отмена", callback_data=cb("gift", "cancel")))
    return text, add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_recipient_results_message(candidates: list, query: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    markup = types.InlineKeyboardMarkup()
    for p in candidates:
        markup.add(types.InlineKeyboardButton(
            f"{p['display_name']} (Эло {round(p['elo'])})", callback_data=cb("gift", "recip", p["id"]),
        ))
    if candidates:
        text = f"Похожие на «{esc(query)}»:"
    else:
        text = f"Никого не нашлось по «{esc(query)}». Попробуй ещё раз или отмени."
    markup.row(types.InlineKeyboardButton("✖️ Отмена", callback_data=cb("gift", "cancel")))
    return text, add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_ask_note_message(recipient_name: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = f"Получатель: <b>{esc(recipient_name)}</b>\n\nНапиши короткую заметку к подарку или пропусти этот шаг."
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("⏭ Без заметки", callback_data=cb("gift", "skip-note")))
    markup.row(types.InlineKeyboardButton("✖️ Отмена", callback_data=cb("gift", "cancel")))
    return text, add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_confirm_message(item_name: str, recipient_name: str, note: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [
        "🎁 <b>Подтверди подарок</b>", "",
        f"Предмет: {esc(item_name)}",
        f"Получатель: {esc(recipient_name)}",
    ]
    if note:
        lines.append(f"Заметка: «{esc(note)}»")
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Отправить", callback_data=cb("gift", "confirm")),
        types.InlineKeyboardButton("✖️ Отмена", callback_data=cb("gift", "cancel")),
    )
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("gift", "hub"))


def build_sent_message(item_name: str, recipient_name: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = f"✅ «{esc(item_name)}» отправлен игроку {esc(recipient_name)}!"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Отправить ещё", callback_data=cb("gift", "send")))
    return text, add_nav_footer(markup, back_target=cb("gift", "hub"))

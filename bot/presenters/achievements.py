from typing import Optional, Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc, truncate


def build_achievements_message(items: list) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    unlocked = [a for a in items if a["unlocked"]]
    lines = [f"🎖 <b>Достижения</b> — {len(unlocked)}/{len(items)}", ""]
    for a in unlocked:
        pin_mark = " 📌" if a.get("pinned") else ""
        lines.append(f"#{a['id']} {esc(a['name'])}{pin_mark} — {esc(a['description'])}")
    if not unlocked:
        lines.append("Пока нет открытых достижений.")

    markup = None
    if unlocked:
        markup = types.InlineKeyboardMarkup()
        for a in unlocked:
            short_name = truncate(a["name"], 28)
            if a.get("pinned"):
                label, action = f"📤 Открепить «{short_name}»", "unpin"
            else:
                label, action = f"📌 Закрепить «{short_name}»", "pin"
            markup.add(types.InlineKeyboardButton(label, callback_data=cb("ach", action, a["id"])))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("profile", "open"))


def build_titles_message(items: list) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    active = [t for t in items if not t["revoked"]]
    lines = ["🏅 <b>Титулы</b>", ""]
    markup = None
    if active:
        markup = types.InlineKeyboardMarkup()
    for t in active:
        equipped_mark = " (экипирован)" if t["equipped"] else ""
        raw_name = t["title"]["name"] if t.get("title") else "?"
        lines.append(f"{esc(raw_name)}{equipped_mark}")
        if t["equipped"]:
            markup.add(types.InlineKeyboardButton("Снять титул", callback_data="v1:title:unequip"))
        else:
            markup.add(types.InlineKeyboardButton(
                f"Экипировать «{truncate(raw_name, 24)}»",
                callback_data=f"v1:title:equip:{t['id']}",
            ))
    if not active:
        lines.append("Пока нет титулов.")
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("profile", "open"))

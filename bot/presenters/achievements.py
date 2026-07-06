from typing import Optional, Tuple

from telebot import types


def build_achievements_message(items: list) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    unlocked = [a for a in items if a["unlocked"]]
    lines = [f"🎖 <b>Достижения</b> — {len(unlocked)}/{len(items)}", ""]
    for a in unlocked:
        pin_mark = " 📌" if a.get("pinned") else ""
        lines.append(f"#{a['id']} {a['name']}{pin_mark} — {a['description']}")
    if not unlocked:
        lines.append("Пока нет открытых достижений.")

    markup = None
    if unlocked:
        markup = types.InlineKeyboardMarkup()
        for a in unlocked:
            if a.get("pinned"):
                label, action = f"📤 Открепить «{a['name']}»", "unpin"
            else:
                label, action = f"📌 Закрепить «{a['name']}»", "pin"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"ach:{action}:{a['id']}"))
    return "\n".join(lines), markup


def build_titles_message(items: list) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    active = [t for t in items if not t["revoked"]]
    lines = ["🏅 <b>Титулы</b>", ""]
    for t in active:
        equipped_mark = " (экипирован)" if t["equipped"] else ""
        title_name = t["title"]["name"] if t.get("title") else "?"
        lines.append(f"{title_name}{equipped_mark}")
    if not active:
        lines.append("Пока нет титулов.")
    return "\n".join(lines), None

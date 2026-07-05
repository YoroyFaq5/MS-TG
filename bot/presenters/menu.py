from telebot import types

MENU_ROWS = [
    ["👤 Профиль", "📊 Статистика"],
    ["🏆 Рейтинг", "📜 История"],
    ["💰 Баланс", "🏅 Достижения"],
    ["🎮 Турниры", "🎯 Fantasy"],
    ["⚙️ Аккаунт"],
]


def build_main_menu_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in MENU_ROWS:
        markup.row(*row)
    return markup

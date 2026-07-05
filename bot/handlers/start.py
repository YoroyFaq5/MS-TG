from bot.telegram_bot import bot
from bot.presenters.start import build_welcome_message


@bot.message_handler(commands=["start"])
def handle_start(message) -> None:
    text, markup = build_welcome_message()
    bot.send_message(message.chat.id, text, reply_markup=markup)

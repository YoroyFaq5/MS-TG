"""
Импорт каждого модуля-хендлера здесь регистрирует его @bot.message_handler/
@bot.callback_query_handler декораторы на общем экземпляре bot из
bot.telegram_bot — сам этот файл импортируется один раз в create_app().
"""
from bot.handlers import start  # noqa: F401
from bot.handlers import profile  # noqa: F401
from bot.handlers import compare  # noqa: F401

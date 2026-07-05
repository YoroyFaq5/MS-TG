"""
Импорт каждого модуля-хендлера здесь регистрирует его @bot.message_handler/
@bot.callback_query_handler декораторы на общем экземпляре bot из
bot.telegram_bot — сам этот файл импортируется один раз в create_app().
"""
from bot.handlers import start  # noqa: F401
from bot.handlers import profile  # noqa: F401
from bot.handlers import compare  # noqa: F401
from bot.handlers import ratings  # noqa: F401
from bot.handlers import history  # noqa: F401
from bot.handlers import economy  # noqa: F401
from bot.handlers import achievements  # noqa: F401
from bot.handlers import tournaments  # noqa: F401
from bot.handlers import fantasy  # noqa: F401
from bot.handlers import account  # noqa: F401
from bot.handlers import inline  # noqa: F401

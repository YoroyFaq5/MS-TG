"""
Импорт каждого модуля-хендлера здесь регистрирует его @bot.message_handler/
@bot.callback_query_handler декораторы на общем экземпляре bot из
bot.telegram_bot — сам этот файл импортируется один раз в create_app().

Порядок важен для message_handler'ов с текстовым фильтром: FSM-перехватчики
свободного текста (gifts.py::handle_gift_*_text, vs.py::handle_vs_search_text)
идут РАНЬШЕ menu.py, чей "🏠 Меню" — тоже текстовый фильтр (Reply Keyboard) —
не должен успеть сработать первым, если telebot остановится на первом
совпадении. Коллизия в любом случае практически невозможна (FSM-фильтры
истинны только для чата, реально находящегося в соответствующем сценарии),
но порядок соблюдён для ясности и на случай будущих сценариев.
"""
from bot.handlers import start  # noqa: F401
from bot.handlers import gifts  # noqa: F401
from bot.handlers import vs  # noqa: F401
from bot.handlers import profile  # noqa: F401
from bot.handlers import compare  # noqa: F401
from bot.handlers import ratings  # noqa: F401
from bot.handlers import seasons  # noqa: F401
from bot.handlers import history  # noqa: F401
from bot.handlers import economy  # noqa: F401
from bot.handlers import achievements  # noqa: F401
from bot.handlers import tournaments  # noqa: F401
from bot.handlers import games  # noqa: F401
from bot.handlers import fantasy  # noqa: F401
from bot.handlers import shop  # noqa: F401
from bot.handlers import inventory  # noqa: F401
from bot.handlers import notif_settings  # noqa: F401
from bot.handlers import account  # noqa: F401
from bot.handlers import inline  # noqa: F401
from bot.handlers import menu  # noqa: F401

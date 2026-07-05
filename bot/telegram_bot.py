"""
Единственное место создания экземпляров TeleBot и ApiClient — синглтоны,
импортируемые хендлерами. threaded=False: мы работаем в синхронной
WSGI-модели (один вебхук-запрос — один процесс update'а), встроенная
многопоточность telebot тут не нужна и не желательна.
"""
import telebot

from bot.config import Config
from bot.api_client import ApiClient

bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN, threaded=False, parse_mode="HTML")

api_client = ApiClient(
    base_url=Config.MAIN_API_BASE_URL,
    service_token=Config.MAIN_API_SERVICE_TOKEN,
    connect_timeout=Config.API_CONNECT_TIMEOUT,
    read_timeout=Config.API_READ_TIMEOUT,
)

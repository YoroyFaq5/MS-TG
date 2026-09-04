"""
Config
======
Тот же стиль, что и в основном проекте (MS/app/config.py) — плоский
os.environ.get(), без тихих fallback'ов на обязательных переменных.
Единообразие между двумя кодовыми базами важнее любой "продвинутой"
библиотеки конфигурации (pydantic-settings и т.п.) — один разработчик,
один способ читать конфиг в обоих проектах.
"""
import os

_REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "TELEGRAM_WEBHOOK_PATH_TOKEN",
    "MAIN_API_BASE_URL",
    "MAIN_API_SERVICE_TOKEN",
    "INCOMING_EVENT_SECRET",
]


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} не задан. См. .env.example — все переменные ниже "
            f"обязательны, тихого fallback нет (та же философия, что и "
            f"DATABASE_URL в основном проекте)."
        )
    return value


class Config:
    TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_SECRET = _require("TELEGRAM_WEBHOOK_SECRET")
    TELEGRAM_WEBHOOK_PATH_TOKEN = _require("TELEGRAM_WEBHOOK_PATH_TOKEN")
    MAIN_API_BASE_URL = _require("MAIN_API_BASE_URL")
    MAIN_API_SERVICE_TOKEN = _require("MAIN_API_SERVICE_TOKEN")
    INCOMING_EVENT_SECRET = _require("INCOMING_EVENT_SECRET")

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    # Опционально — см. bot/bot_identity.py: без него бот один раз узнаёт
    # своё имя через bot.get_me() и кеширует на время работы процесса;
    # заданное явно — экономит этот один сетевой вызов при первом запросе.
    TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME")

    # Антиспам для команд общего чата (CLAUDE_TASK_BOT_RU_GROUPS.md, п.7) —
    # по паре (chat_id, user_id), отдельно от общего вебхук-лимитера.
    GROUP_COMMAND_LIMIT_SHORT = int(os.environ.get("GROUP_COMMAND_LIMIT_SHORT", "5"))
    GROUP_COMMAND_WINDOW_SHORT_SECONDS = int(os.environ.get("GROUP_COMMAND_WINDOW_SHORT_SECONDS", "20"))
    GROUP_COMMAND_LIMIT_LONG = int(os.environ.get("GROUP_COMMAND_LIMIT_LONG", "20"))
    GROUP_COMMAND_WINDOW_LONG_SECONDS = int(os.environ.get("GROUP_COMMAND_WINDOW_LONG_SECONDS", "300"))

    # Таймауты исходящих запросов к API основного сайта (секунды).
    API_CONNECT_TIMEOUT = float(os.environ.get("API_CONNECT_TIMEOUT", "5"))
    API_READ_TIMEOUT = float(os.environ.get("API_READ_TIMEOUT", "10"))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

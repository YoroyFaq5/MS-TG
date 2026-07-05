"""
Логирование — стандартный logging, без внешних зависимостей.
WARNING зарезервирован за провалами проверки подписи/авторизации,
чтобы такие события были заметны в логе отдельно от обычных ошибок сети.
"""
import logging
import sys


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

"""
Обработка входящих fire-and-forget событий ОТ основного сайта (MS) —
подпись уже проверена в bot/__init__.py::incoming_event, а дедупликация по
event_id (если сайт его передал) — тоже там, один раз для всего события
(next-slot фанится на нескольких получателей, но это по-прежнему ОДНО
событие с одним X-Event-Id). Каждый тип события — своя функция, реестр
EVENT_HANDLERS ниже; dispatch() возвращает False для неизвестных типов
(роут отвечает 501, а не падает).

Presenters теперь возвращают (text, markup, category) — category — один из
bot.storage.NOTIFICATION_CATEGORIES, проверяется здесь ПЕРЕД отправкой,
чтобы уважать пользовательские настройки уведомлений (/ 🔔 Уведомления
в главном меню).
"""
import logging

from bot import storage
from bot.presenters.notifications import (
    build_next_slot_message,
    build_achievement_granted_message,
    build_title_granted_message,
    build_item_bought_out_message,
    build_fantasy_result_message,
    build_fantasy_prize_message,
    build_gift_received_message,
    build_season_award_message,
    build_game_finished_message,
)

logger = logging.getLogger(__name__)


def _send(telegram_id, text: str, markup, category: str) -> None:
    from bot.telegram_bot import bot

    if not telegram_id:
        return
    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError):
        return
    if not storage.is_notification_enabled(telegram_id, category):
        return
    try:
        bot.send_message(telegram_id, text, reply_markup=markup)
    except Exception:
        # Сбой отправки одному игроку (например, он ни разу не нажал
        # /start в диалоге с ботом — Telegram не даст написать первым)
        # не должен прерывать рассылку остальным.
        logger.exception("Не удалось отправить уведомление (категория %s) telegram_id=%s", category, telegram_id)


def handle_next_slot(payload: dict) -> None:
    for player in payload.get("players", []):
        telegram_id = player.get("telegram_id")
        if not telegram_id:
            continue
        text, markup, category = build_next_slot_message(player)
        _send(telegram_id, text, markup, category)


def _make_simple_handler(builder):
    """
    Большинство событий (в отличие от next-slot) — один получатель,
    telegram_id прямо в payload. Общий шаблон вместо восьми одинаковых
    функций: собрать (текст, клавиатуру, категорию) пресентером, проверить
    настройки получателя, отправить, залогировать и проглотить сбой
    отправки (тот же принцип, что и next-slot).
    """
    def handler(payload: dict) -> None:
        telegram_id = payload.get("telegram_id")
        if not telegram_id:
            return
        text, markup, category = builder(payload)
        _send(telegram_id, text, markup, category)
    handler.__name__ = f"handle_{builder.__name__}"
    return handler


EVENT_HANDLERS = {
    "next-slot": handle_next_slot,
    "achievement-granted": _make_simple_handler(build_achievement_granted_message),
    "title-granted": _make_simple_handler(build_title_granted_message),
    "item-bought-out": _make_simple_handler(build_item_bought_out_message),
    "fantasy-result": _make_simple_handler(build_fantasy_result_message),
    "fantasy-prize": _make_simple_handler(build_fantasy_prize_message),
    "gift-received": _make_simple_handler(build_gift_received_message),
    "season-award": _make_simple_handler(build_season_award_message),
    "game-finished": _make_simple_handler(build_game_finished_message),
}


def dispatch(event_type: str, payload: dict) -> bool:
    handler = EVENT_HANDLERS.get(event_type)
    if not handler:
        logger.info("Неизвестный тип события: %s", event_type)
        return False
    handler(payload)
    return True

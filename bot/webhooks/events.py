"""
Обработка входящих fire-and-forget событий ОТ основного сайта (MS) —
подпись уже проверена в bot/__init__.py::incoming_event ДО того, как
payload попадает сюда. Каждый тип события — своя функция, реестр
EVENT_HANDLERS ниже; dispatch() возвращает False для неизвестных типов
(роут отвечает 501, а не падает).
"""
import logging

from bot.presenters.notifications import build_next_slot_message

logger = logging.getLogger(__name__)


def handle_next_slot(payload: dict) -> None:
    from bot.telegram_bot import bot

    for player in payload.get("players", []):
        telegram_id = player.get("telegram_id")
        if not telegram_id:
            continue
        text = build_next_slot_message(player)
        try:
            bot.send_message(int(telegram_id), text)
        except Exception:
            # Сбой отправки одному игроку (например, он ни разу не нажал
            # /start в диалоге с ботом — Telegram не даст написать первым)
            # не должен прерывать рассылку остальным.
            logger.exception(
                "Не удалось отправить next-slot уведомление telegram_id=%s", telegram_id
            )


EVENT_HANDLERS = {
    "next-slot": handle_next_slot,
}


def dispatch(event_type: str, payload: dict) -> bool:
    handler = EVENT_HANDLERS.get(event_type)
    if not handler:
        logger.info("Неизвестный тип события: %s", event_type)
        return False
    handler(payload)
    return True

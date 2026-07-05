"""
Обработка входящих fire-and-forget событий ОТ основного сайта (MS) —
подпись уже проверена в bot/__init__.py::incoming_event ДО того, как
payload попадает сюда. Каждый тип события — своя функция, реестр
EVENT_HANDLERS ниже; dispatch() возвращает False для неизвестных типов
(роут отвечает 501, а не падает).
"""
import logging

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


def _make_simple_handler(builder):
    """
    Большинство событий (в отличие от next-slot) — один получатель,
    telegram_id прямо в payload. Общий шаблон вместо восьми одинаковых
    функций: собрать текст пресентером, отправить, залогировать и
    проглотить сбой отправки (тот же принцип, что и next-slot).
    """
    def handler(payload: dict) -> None:
        from bot.telegram_bot import bot

        telegram_id = payload.get("telegram_id")
        if not telegram_id:
            return
        text = builder(payload)
        try:
            bot.send_message(int(telegram_id), text)
        except Exception:
            logger.exception(
                "Не удалось отправить уведомление (%s) telegram_id=%s",
                builder.__name__, telegram_id,
            )
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

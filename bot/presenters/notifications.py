"""
Presenters для входящих событий ОТ основного сайта (не Telegram-апдейтов)
— так же чистые функции без I/O, как и остальные presenters/*.
"""


def build_next_slot_message(player: dict) -> str:
    tournament = player.get("tournament_name") or "турнире"
    round_number = player.get("round_number")
    table_number = player.get("table_number")
    seat_number = player.get("seat_number")
    return (
        f"🎲 Новый раунд в «{tournament}»!\n"
        f"Раунд {round_number}, стол №{table_number}.\n"
        f"Твой слот — <b>{seat_number}</b>."
    )


def build_achievement_granted_message(payload: dict) -> str:
    return f"🎖 Новое достижение: <b>{payload['achievement_name']}</b>!"


def build_title_granted_message(payload: dict) -> str:
    return f"🏅 Вам выдан титул: <b>{payload['title_name']}</b>!"


def build_item_bought_out_message(payload: dict) -> str:
    return (
        f"💰 Ваш предмет «{payload['item_name']}» перекупил {payload['buyer_name']} "
        f"за {payload['offer_price']:.0f} монет — вам зачислено {payload['payout']:.0f}."
    )


def build_fantasy_result_message(payload: dict) -> str:
    return f"🎯 Fantasy: турнир «{payload['tournament_name']}» — {payload['points']} очков."


def build_fantasy_prize_message(payload: dict) -> str:
    return (
        f"🎉 Fantasy: {payload['place']} место в «{payload['tournament_name']}» — "
        f"+{payload['amount']:.0f} монет!"
    )


def build_gift_received_message(payload: dict) -> str:
    text = f"🎁 {payload['sender_name']} подарил(а) вам «{payload['item_name']}»!"
    if payload.get("message"):
        text += f"\n«{payload['message']}»"
    return text


def build_season_award_message(payload: dict) -> str:
    return f"🏆 Сезон «{payload['season_name']}»: место #{payload['rank']} — +{payload['amount']:.0f} монет!"


def build_game_finished_message(payload: dict) -> str:
    icon = "✅" if payload["won"] else "❌"
    text = f"{icon} Игра завершена — {payload['total_score']} балл."
    if payload.get("bonus_score"):
        text += f" (бонус {payload['bonus_score']:+.1f})"
    return text

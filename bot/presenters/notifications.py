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

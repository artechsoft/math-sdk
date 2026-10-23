"Handles independent simulation events and details."

from copy import deepcopy


def copy_event(value):
    """Copy JSON-like event data much faster than deepcopy. Other types fall back to deepcopy."""
    t = type(value)
    if t is dict:
        return {k: copy_event(v) for k, v in value.items()}
    if t is list:
        return [copy_event(v) for v in value]
    if t is str or t is int or t is float or t is bool or value is None:
        return value
    return deepcopy(value)


class Book:
    "Stores simulation information."

    def __init__(self, book_id: int, criteria: str):
        "Initialize simulation book"
        self.id = book_id
        self.payout_multiplier = 0.0
        self.events = []
        self.criteria = criteria
        self.basegame_wins = 0.0
        self.freegame_wins = 0.0

    def add_event(self, event: dict):
        "Append event to book."
        self.events.append(copy_event(event))

    def append_book_items(self, event_id: int, appended_info: dict):
        "Modify an existing book event at position 'event_id'"
        for k, v in appended_info.items():
            self.events[event_id][k] = v

    def to_json(self):
        "Return JSON-ready object."
        json_book = {
            "id": self.id,
            "payoutMultiplier": int(round(self.payout_multiplier * 100, 0)),
            "events": self.events,
            "criteria": self.criteria,
            "baseGameWins": self.basegame_wins,
            "freeGameWins": self.freegame_wins,
        }
        return json_book

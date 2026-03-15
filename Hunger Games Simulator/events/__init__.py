import random
from typing import List
from core.game_state import GameState
from utils.filter import work_friendly
from events.arena_events import trigger_random_arena_event

def trigger_random_event(game: GameState) -> str:
    """
    Triggers a random arena event and applies effects.
    Returns description of the event.
    """
    def get_message(*args, **kwargs):
        # Simple message getter for arena events
        return f"{' '.join(args)} {' '.join(f'{k}={v}' for k, v in kwargs.items())}"

    event_messages = trigger_random_arena_event(game, get_message)
    if event_messages:
        return work_friendly(" ".join(event_messages))
    return ""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class FieldState:
    weather: str | None = None
    terrain: str | None = None
    trick_room_turns: int = 0
    tailwind_player_turns: int = 0
    tailwind_opponent_turns: int = 0

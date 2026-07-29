from __future__ import annotations
from dataclasses import dataclass

ACTION_MOVE = "move"
ACTION_SWITCH = "switch"


@dataclass(frozen=True)
class Action:
    action_type: str
    move: str | None = None
    switch_index: int | None = None

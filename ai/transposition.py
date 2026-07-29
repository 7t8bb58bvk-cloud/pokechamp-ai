from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TTEntry:
    depth: int
    score: float
    flag: str
    action: object | None = None


class TranspositionTable:
    def __init__(self):
        self._table: dict[tuple, TTEntry] = {}

    @staticmethod
    def key_from_state(state) -> tuple:
        def pack_pokemon(p):
            return (
                p.name,
                p.current_hp,
                tuple(sorted(getattr(p, "boosts", {}).items())),
                getattr(p, "status", None),
                getattr(p, "item", ""),
                getattr(p, "ability", ""),
            )

        return (
            state.turn,
            pack_pokemon(state.player),
            pack_pokemon(state.opponent),
            state.field.weather,
            state.field.terrain,
            state.field.trick_room_turns,
            state.field.tailwind_player_turns,
            state.field.tailwind_opponent_turns,
        )

    def get(self, state, depth: int):
        entry = self._table.get(self.key_from_state(state))
        if entry and entry.depth >= depth:
            return entry
        return None

    def put(self, state, depth: int, score: float, flag: str, action=None):
        self._table[self.key_from_state(state)] = TTEntry(depth=depth, score=score, flag=flag, action=action)

    def __len__(self):
        return len(self._table)

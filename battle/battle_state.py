from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from battle.field import FieldState


@dataclass
class BattleState:
    player_side: object
    opponent_side: object
    turn: int = 1
    log: list[str] = field(default_factory=list)
    field: FieldState = field(default_factory=FieldState)

    @property
    def player(self):
        return self.player_side.active

    @property
    def opponent(self):
        return self.opponent_side.active

    def battle_over(self) -> bool:
        return self.player.current_hp <= 0 or self.opponent.current_hp <= 0

    def winner(self) -> str:
        if self.player.current_hp <= 0 and self.opponent.current_hp <= 0:
            return "draw"
        if self.player.current_hp <= 0:
            return "opponent"
        if self.opponent.current_hp <= 0:
            return "player"
        return "ongoing"

    def next_turn(self):
        self.turn += 1
        self.player.volatile_status.pop("protect", None)
        self.opponent.volatile_status.pop("protect", None)
        if self.field.tailwind_player_turns > 0:
            self.field.tailwind_player_turns -= 1
        if self.field.tailwind_opponent_turns > 0:
            self.field.tailwind_opponent_turns -= 1
        if self.field.trick_room_turns > 0:
            self.field.trick_room_turns -= 1

    def copy(self):
        return deepcopy(self)

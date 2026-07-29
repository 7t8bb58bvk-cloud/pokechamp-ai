from __future__ import annotations
from dataclasses import dataclass


@dataclass
class EffectResult:
    applied: bool
    message: str = ""


class EffectEngine:
    @staticmethod
    def apply_status_after_move(state, attacker, defender, move):
        name = str(getattr(move, "name", "")).lower()
        if name == "will-o-wisp" and defender.status is None:
            defender.status = "burn"
            state.log.append(f"{defender.name} was burned")
            return EffectResult(True, f"{defender.name} burned")
        return EffectResult(False, "")

    @staticmethod
    def end_of_turn(state):
        for side in (state.player_side, state.opponent_side):
            p = side.active
            if p.status == "burn":
                dmg = max(1, p.max_hp // 16)
                p.current_hp = max(0, p.current_hp - dmg)
                state.log.append(f"{p.name} was hurt by burn for {dmg}")
            if p.status == "poison":
                dmg = max(1, p.max_hp // 8)
                p.current_hp = max(0, p.current_hp - dmg)
                state.log.append(f"{p.name} was hurt by poison for {dmg}")

from __future__ import annotations

from data.move_database import get_move
from engine.stat_engine import calculate_speed


def show_battle_summary(state):
    print("TURN:", state.turn)
    print("FIELD:", state.field)
    print("PLAYER:", state.player.name, state.player.current_hp, "/", state.player.max_hp)
    print("OPP   :", state.opponent.name, state.opponent.current_hp, "/", state.opponent.max_hp)
    print("SPEED :", calculate_speed(state.player, state.field, "player"), calculate_speed(state.opponent, state.field, "opponent"))


def available_moves(pokemon):
    out = []
    for name in getattr(pokemon, "moves", []):
        mv = get_move(name)
        if mv is not None:
            out.append(mv)
    return out


def is_offensive_move(move_name: str) -> bool:
    mv = get_move(move_name)
    return bool(mv and mv.category in ("physical", "special") and mv.power > 0)

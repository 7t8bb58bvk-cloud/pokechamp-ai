from __future__ import annotations

from engine.damage_core_v2 import damage_rolls


def _first_move_name(pokemon):
    for m in getattr(pokemon, "moves", []) or []:
        if m:
            return m
    return None


def switch_value(state, switch_index: int, side_name: str = "player") -> float:
    me_side = state.player_side if side_name == "player" else state.opponent_side
    me = state.player if side_name == "player" else state.opponent
    opp = state.opponent if side_name == "player" else state.player

    if switch_index < 0 or switch_index >= len(getattr(me_side, "team", [])):
        return -100000.0

    target = me_side.team[switch_index]
    if getattr(target, "fainted", False):
        return -100000.0

    score = 0.0
    opp_move = _first_move_name(opp)

    if opp_move is not None:
        try:
            incoming = damage_rolls(opp, me, opp_move, state.field)
            score += max(0.0, float(incoming.avg_damage) - float(me.current_hp)) * 2.5
            if incoming.avg_damage >= me.current_hp:
                score += 180.0
            elif incoming.avg_damage >= me.current_hp * 0.75:
                score += 90.0
        except Exception:
            pass

    hp_ratio = target.current_hp / max(1, target.max_hp)
    score += hp_ratio * 120.0

    best_offense = 0.0
    for move in getattr(target, "moves", []) or []:
        try:
            prof = damage_rolls(target, opp, move, state.field)
            v = float(prof.avg_damage) + float(prof.ko_chance) * 3500.0
            if v > best_offense:
                best_offense = v
        except Exception:
            pass
    score += best_offense * 0.8

    if opp_move is not None:
        try:
            incoming_switch = damage_rolls(opp, target, opp_move, state.field)
            current_incoming = damage_rolls(opp, me, opp_move, state.field)
            score += max(0.0, float(current_incoming.avg_damage) - float(incoming_switch.avg_damage)) * 1.2
        except Exception:
            pass

    boosts = getattr(target, "boosts", {}) or {}
    score += boosts.get("spe", 0) * 10.0
    score += boosts.get("atk", 0) * 8.0 + boosts.get("spa", 0) * 8.0
    return float(score)

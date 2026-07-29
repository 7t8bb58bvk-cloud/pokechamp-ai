from __future__ import annotations

from engine.exact_mechanics import damage_rolls
from engine.stat_engine import calculate_speed


def _first_move_name(pokemon):
    for m in getattr(pokemon, "moves", []) or []:
        if m:
            return m
    return None


def action_value(state, action, side_name="player"):
    """
    Immediate action heuristic.

    Positive = better move
    Negative = bad move
    """

    if action is None:
        return -100000.0

    if side_name == "player":
        me = state.player
        opp = state.opponent
    else:
        me = state.opponent
        opp = state.player

    score = 0.0

    if getattr(action, "action_type", "") == "switch":

        hp_ratio = me.current_hp / max(1, me.max_hp)

        if hp_ratio < 0.30:
            score += 120

        else:
            score += 20

        return float(score)

    move = str(getattr(action, "move", "")).lower()

    try:
        profile = damage_rolls(
            me,
            opp,
            action.move,
            state.field,
        )
    except Exception:
        return -9999.0

    score += profile.avg_damage * 2.2

    score += profile.ko_chance * 5000

    if profile.avg_damage >= opp.current_hp:
        score += 6000

    try:

        my_speed = calculate_speed(
            me,
            state.field,
            side_name,
        )

        opp_speed = calculate_speed(
            opp,
            state.field,
            "opponent" if side_name == "player" else "player",
        )

        score += (my_speed - opp_speed) * 1.8

    except Exception:
        pass

    if profile.avg_damage >= opp.current_hp:
        score += 8000

    if move == "protect":
        opp_move = _first_move_name(opp)
        if opp_move is None:
            score -= 300
        else:
            try:
                opp_profile = damage_rolls(
                    opp,
                    me,
                    opp_move,
                    state.field,
                )
                hp_ratio = me.current_hp / max(1, me.max_hp)

                if opp_profile.avg_damage >= me.current_hp * 0.9:
                    score += 160

                elif hp_ratio < 0.30:
                    score += 60

                else:
                    score -= 900
            except Exception:
                score -= 500

    if move in ("swords-dance", "dragon-dance", "calm-mind"):
        hp_ratio = me.current_hp / max(1, me.max_hp)

        if hp_ratio > 0.60:
            score += 220

        elif hp_ratio > 0.40:
            score += 80

        else:
            score -= 160

    if move == "recover":
        hp_ratio = me.current_hp / max(1, me.max_hp)

        if hp_ratio <= 0.55:
            score += 260

        else:
            score -= 100

    if move == "tailwind":
        turns = 0
        if side_name == "player":
            turns = getattr(state.field, "tailwind_player_turns", 0)
        else:
            turns = getattr(state.field, "tailwind_opponent_turns", 0)

        if turns == 0:
            score += 220
        else:
            score -= 100

    if move not in ("protect", "recover", "tailwind", "swords-dance", "dragon-dance", "calm-mind"):
        opp_move = _first_move_name(opp)

        if opp_move is not None:
            try:
                opp_profile = damage_rolls(
                    opp,
                    me,
                    opp_move,
                    state.field,
                )
                score += max(0.0, float(profile.avg_damage) - float(opp_profile.avg_damage)) * 0.8
            except Exception:
                pass

    if profile.ko_chance > 0.4:
        score += 500

    return float(score)

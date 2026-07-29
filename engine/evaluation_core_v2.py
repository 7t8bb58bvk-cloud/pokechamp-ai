from __future__ import annotations

from math import exp

from engine.exact_mechanics import damage_rolls
from engine.stat_engine import calculate_speed


def _first_move_name(pokemon):
    for m in getattr(pokemon, "moves", []) or []:
        if m:
            return m
    return None


def _best_damage_profile(attacker, defender, field):
    best_prof = None
    best_value = -10**18
    for move_name in getattr(attacker, "moves", []) or []:
        try:
            prof = damage_rolls(attacker, defender, move_name, field)
        except Exception:
            continue
        # Prefer moves that actually convert into progress.
        value = (
            float(prof.avg_damage) * 1.25
            + float(prof.ko_chance) * 2500.0
        )
        move = str(move_name).lower()
        if move in ("earthquake", "surf", "thunderbolt", "moonblast", "shadow-ball", "flamethrower", "ice-beam", "dragon-claw"):
            value += 35.0
        if move in ("swords-dance", "dragon-dance", "calm-mind", "tailwind"):
            value += 20.0
        if move == "recover":
            value += 10.0
        if move == "protect":
            value -= 180.0
        if value > best_value:
            best_value = value
            best_prof = prof
    return best_prof, best_value


def _score_to_winprob(score: float) -> float:
    # steeper than previous version so evaluation separates moves more clearly
    return 1.0 / (1.0 + exp(-score / 300.0))


class EvaluationEngineV2:
    @staticmethod
    def evaluate(state) -> float:
        if state.player.current_hp <= 0:
            return -30000.0
        if state.opponent.current_hp <= 0:
            return 30000.0

        hp_player = state.player.current_hp / max(1, state.player.max_hp)
        hp_opp = state.opponent.current_hp / max(1, state.opponent.max_hp)
        alive_player = state.player_side.alive_count()
        alive_opp = state.opponent_side.alive_count()

        sp_player = calculate_speed(state.player, state.field, "player")
        sp_opp = calculate_speed(state.opponent, state.field, "opponent")

        p_best_prof, p_best_value = _best_damage_profile(state.player, state.opponent, state.field)
        o_best_prof, o_best_value = _best_damage_profile(state.opponent, state.player, state.field)

        p_best_prof = p_best_prof if p_best_prof is not None else None
        o_best_prof = o_best_prof if o_best_prof is not None else None

        p_best_dmg = p_best_prof.avg_damage if p_best_prof is not None else 0.0
        o_best_dmg = o_best_prof.avg_damage if o_best_prof is not None else 0.0
        p_best_ko = p_best_prof.ko_chance if p_best_prof is not None else 0.0
        o_best_ko = o_best_prof.ko_chance if o_best_prof is not None else 0.0

        score = 0.0

        # Core position
        score += 3000.0 * (hp_player - hp_opp)
        score += 1500.0 * (alive_player - alive_opp)
        score += 8.0 * (sp_player - sp_opp)

        # Damage race
        score += 2.5 * (p_best_dmg - o_best_dmg)
        score += 3500.0 * (p_best_ko - o_best_ko)
        score += 0.5 * (p_best_value - o_best_value)

        # Direct conversion
        if p_best_dmg >= state.opponent.current_hp:
            score += 8000.0
        if o_best_dmg >= state.player.current_hp:
            score -= 8000.0

        # Low HP urgency
        if hp_player < 0.35:
            score -= 150.0
        if hp_opp < 0.35:
            score += 150.0

        # Setup only if it is likely to convert to pressure
        boosts_p = getattr(state.player, "boosts", {}) or {}
        boosts_o = getattr(state.opponent, "boosts", {}) or {}
        score += 28.0 * (boosts_p.get("atk", 0) - boosts_o.get("atk", 0))
        score += 28.0 * (boosts_p.get("spa", 0) - boosts_o.get("spa", 0))
        score += 18.0 * (boosts_p.get("spe", 0) - boosts_o.get("spe", 0))
        score += 12.0 * (boosts_p.get("def", 0) - boosts_o.get("def", 0))
        score += 12.0 * (boosts_p.get("spd", 0) - boosts_o.get("spd", 0))

        # Field control
        if getattr(state.field, "tailwind_player_turns", 0) > 0:
            score += 75.0
        if getattr(state.field, "tailwind_opponent_turns", 0) > 0:
            score -= 75.0
        if getattr(state.field, "trick_room_turns", 0) > 0:
            score += (sp_opp - sp_player) * 0.12

        # Status
        if getattr(state.opponent, "status", None) in ("burn", "poison", "paralysis"):
            score += 120.0
        if getattr(state.player, "status", None) in ("burn", "poison", "paralysis"):
            score -= 120.0

        # Explicit stall punishment
        protect_streak = int(state.player.volatile_status.get("protect_streak", 0))
        if protect_streak > 0:
            score -= 500.0 * protect_streak

        # Extra penalty if we're healthy and not under lethal threat, but still stalling.
        opp_move = _first_move_name(state.opponent)
        if opp_move is not None:
            try:
                opp_prof = damage_rolls(state.opponent, state.player, opp_move, state.field)
                if hp_player > 0.55 and opp_prof.avg_damage < state.player.current_hp * 0.75:
                    score -= 180.0 * max(1, protect_streak)
            except Exception:
                pass

        # Favor momentum if we are already advantaged
        if hp_player > hp_opp and alive_player >= alive_opp:
            score += 120.0

        # Slight smoothing
        score += (_score_to_winprob(score) - 0.5) * 300.0

        return float(score)

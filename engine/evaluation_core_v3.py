from __future__ import annotations

from math import exp
from engine.damage_core_v2 import damage_rolls
from engine.stat_core_v2 import calculate_speed

def _first_move_name(pokemon):
    for m in getattr(pokemon, "moves", []) or []:
        if m:
            return m
    return None

def _winprob(score: float) -> float:
    return 1.0 / (1.0 + exp(-score / 300.0))

def _best_damage(attacker, defender, field):
    best_prof = None
    best_val = -10**18
    for move in getattr(attacker, "moves", []) or []:
        if not move:
            continue
        try:
            prof = damage_rolls(attacker, defender, move, field)
        except Exception:
            continue
        val = prof.avg_damage * 1.4 + prof.ko_chance * 3500.0
        m = str(move).lower()
        if m in ("earthquake", "surf", "thunderbolt", "moonblast", "shadow-ball", "flamethrower", "ice-beam", "dragon-claw"):
            val += 40.0
        if m in ("swords-dance", "dragon-dance", "calm-mind", "tailwind"):
            val += 25.0
        if m == "protect":
            val -= 250.0
        if m == "recover":
            val += 20.0
        if val > best_val:
            best_val = val
            best_prof = prof
    return best_prof, best_val

class EvaluationEngineV3:
    @staticmethod
    def evaluate(state) -> float:
        if state.player.current_hp <= 0:
            return -30000.0
        if state.opponent.current_hp <= 0:
            return 30000.0

        hp_p = state.player.current_hp / max(1, state.player.max_hp)
        hp_o = state.opponent.current_hp / max(1, state.opponent.max_hp)
        alive_p = state.player_side.alive_count()
        alive_o = state.opponent_side.alive_count()

        sp_p = calculate_speed(state.player, state.field, "player")
        sp_o = calculate_speed(state.opponent, state.field, "opponent")

        p_best, p_val = _best_damage(state.player, state.opponent, state.field)
        o_best, o_val = _best_damage(state.opponent, state.player, state.field)

        p_dmg = p_best.avg_damage if p_best is not None else 0.0
        o_dmg = o_best.avg_damage if o_best is not None else 0.0
        p_ko = p_best.ko_chance if p_best is not None else 0.0
        o_ko = o_best.ko_chance if o_best is not None else 0.0

        score = 0.0
        score += 3400.0 * (hp_p - hp_o)
        score += 1600.0 * (alive_p - alive_o)
        score += 8.0 * (sp_p - sp_o)
        score += 2.8 * (p_dmg - o_dmg)
        score += 4000.0 * (p_ko - o_ko)
        score += 0.55 * (p_val - o_val)

        if p_dmg >= state.opponent.current_hp:
            score += 9000.0
        if o_dmg >= state.player.current_hp:
            score -= 9000.0

        if hp_p < 0.35:
            score -= 200.0
        if hp_o < 0.35:
            score += 200.0

        bp = getattr(state.player, "boosts", {}) or {}
        bo = getattr(state.opponent, "boosts", {}) or {}
        for stat, w in (("atk", 30.0), ("spa", 30.0), ("spe", 20.0), ("def", 12.0), ("spd", 12.0)):
            score += w * (bp.get(stat, 0) - bo.get(stat, 0))

        if getattr(state.field, "tailwind_player_turns", 0) > 0:
            score += 90.0
        if getattr(state.field, "tailwind_opponent_turns", 0) > 0:
            score -= 90.0
        if getattr(state.field, "trick_room_turns", 0) > 0:
            score += (sp_o - sp_p) * 0.15

        if getattr(state.opponent, "status", None) in ("burn", "poison", "paralysis"):
            score += 150.0
        if getattr(state.player, "status", None) in ("burn", "poison", "paralysis"):
            score -= 150.0

        protect_streak = int(state.player.volatile_status.get("protect_streak", 0))
        if protect_streak > 0:
            score -= 700.0 * protect_streak

        opp_move = _first_move_name(state.opponent)
        if opp_move is not None and hp_p > 0.55:
            try:
                opp_prof = damage_rolls(state.opponent, state.player, opp_move, state.field)
                if opp_prof.avg_damage < state.player.current_hp * 0.75:
                    score -= 180.0 * max(1, protect_streak)
            except Exception:
                pass

        score += (_winprob(score) - 0.5) * 350.0
        return float(score)

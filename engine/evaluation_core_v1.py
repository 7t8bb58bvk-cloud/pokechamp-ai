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
    best = None
    best_score = -1.0
    for move_name in getattr(attacker, "moves", []) or []:
        try:
            prof = damage_rolls(attacker, defender, move_name, field)
        except Exception:
            continue
        score = float(prof.avg_damage) + float(prof.ko_chance) * 1500.0
        if score > best_score:
            best = prof
            best_score = score
    return best, best_score


def _win_probability_from_score(score: float) -> float:
    # Smooth curve, but not too flat.
    return 1.0 / (1.0 + exp(-score / 450.0))


class EvaluationEngineV1:
    @staticmethod
    def evaluate(state) -> float:
        # terminal states
        if state.player.current_hp <= 0:
            return -25000.0
        if state.opponent.current_hp <= 0:
            return 25000.0

        hp_player = state.player.current_hp / max(1, state.player.max_hp)
        hp_opp = state.opponent.current_hp / max(1, state.opponent.max_hp)
        alive_player = state.player_side.alive_count()
        alive_opp = state.opponent_side.alive_count()

        sp_player = calculate_speed(state.player, state.field, "player")
        sp_opp = calculate_speed(state.opponent, state.field, "opponent")

        # Best immediate damage each side can do.
        player_best_prof, player_best_score = _best_damage_profile(state.player, state.opponent, state.field)
        opp_best_prof, opp_best_score = _best_damage_profile(state.opponent, state.player, state.field)

        player_best_damage = player_best_prof.avg_damage if player_best_prof is not None else 0.0
        opp_best_damage = opp_best_prof.avg_damage if opp_best_prof is not None else 0.0
        player_best_ko = player_best_prof.ko_chance if player_best_prof is not None else 0.0
        opp_best_ko = opp_best_prof.ko_chance if opp_best_prof is not None else 0.0

        score = 0.0

        # Material and tempo.
        score += 2600.0 * (hp_player - hp_opp)
        score += 1200.0 * (alive_player - alive_opp)
        score += 5.0 * (sp_player - sp_opp)

        # Immediate damage race.
        score += 2.0 * (player_best_damage - opp_best_damage)
        score += 1800.0 * (player_best_ko - opp_best_ko)

        # Convertible pressure.
        if player_best_damage >= state.opponent.current_hp:
            score += 2200.0
        if opp_best_damage >= state.player.current_hp:
            score -= 2200.0

        # Two-turn pressure.
        if player_best_damage * 2 >= state.opponent.current_hp:
            score += 250.0
        if opp_best_damage * 2 >= state.player.current_hp:
            score -= 250.0

        # Setup and board control.
        boosts_player = getattr(state.player, "boosts", {}) or {}
        boosts_opp = getattr(state.opponent, "boosts", {}) or {}
        score += 24.0 * (boosts_player.get("atk", 0) - boosts_opp.get("atk", 0))
        score += 24.0 * (boosts_player.get("spa", 0) - boosts_opp.get("spa", 0))
        score += 16.0 * (boosts_player.get("spe", 0) - boosts_opp.get("spe", 0))
        score += 10.0 * (boosts_player.get("def", 0) - boosts_opp.get("def", 0))
        score += 10.0 * (boosts_player.get("spd", 0) - boosts_opp.get("spd", 0))

        # Field effects.
        if getattr(state.field, "tailwind_player_turns", 0) > 0:
            score += 45.0
        if getattr(state.field, "tailwind_opponent_turns", 0) > 0:
            score -= 45.0
        if getattr(state.field, "trick_room_turns", 0) > 0:
            score += (sp_opp - sp_player) * 0.1

        # Status pressure.
        if getattr(state.opponent, "status", None) in ("burn", "poison", "paralysis"):
            score += 70.0
        if getattr(state.player, "status", None) in ("burn", "poison", "paralysis"):
            score -= 70.0

        # Penalize repeated passive play very strongly.
        protect_streak = int(state.player.volatile_status.get("protect_streak", 0))
        if protect_streak > 0:
            score -= 200.0 * protect_streak
            if hp_player > 0.55 and opp_best_damage < state.player.current_hp * 0.8:
                score -= 150.0 * protect_streak

        # Penalize hopeless stalling if we have strong offensive options.
        if player_best_damage > 0 and hp_player > 0.5 and opp_best_damage < state.player.current_hp * 0.75:
            score -= 25.0

        # If switching is obviously good, slightly recognize it.
        player_move_names = [m for m in getattr(state.player, "moves", []) or [] if m]
        if player_move_names:
            has_offense = any(
                getattr(damage_rolls(state.player, state.opponent, m, state.field), "avg_damage", 0) > 0
                for m in player_move_names
            )
            if has_offense:
                score += 5.0

        # Smooth final score a bit.
        score += (_win_probability_from_score(score) - 0.5) * 250.0

        return float(score)

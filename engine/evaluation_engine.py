from __future__ import annotations
from engine.stat_engine import calculate_speed


class EvaluationEngine:
    @staticmethod
    def evaluate(state) -> float:
        if state.player.current_hp <= 0:
            return -10_000
        if state.opponent.current_hp <= 0:
            return 10_000

        hp_player = state.player.current_hp / max(1, state.player.max_hp)
        hp_opp = state.opponent.current_hp / max(1, state.opponent.max_hp)

        alive_player = state.player_side.alive_count()
        alive_opp = state.opponent_side.alive_count()

        speed_player = calculate_speed(state.player, state.field, "player")
        speed_opp = calculate_speed(state.opponent, state.field, "opponent")

        boost_score = 0
        for s, w in (("atk", 3), ("def", 2), ("spa", 3), ("spd", 2), ("spe", 3)):
            boost_score += (state.player.boosts.get(s, 0) - state.opponent.boosts.get(s, 0)) * w

        score = 1000 * (hp_player - hp_opp)
        score += 250 * (alive_player - alive_opp)
        score += 2 * (speed_player - speed_opp)
        score += 25 * boost_score
        return float(score)

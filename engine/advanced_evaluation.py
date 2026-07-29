from __future__ import annotations
from engine.evaluation_engine import EvaluationEngine
from engine.win_probability import WinProbability
from engine.stat_engine import calculate_speed


class AdvancedEvaluationEngine:
    @staticmethod
    def evaluate(state) -> float:
        base = EvaluationEngine.evaluate(state)
        p = WinProbability.estimate_from_state(state)

        # small bonuses for having speed control / damage status / field control
        speed_player = calculate_speed(state.player, state.field, "player")
        speed_opp = calculate_speed(state.opponent, state.field, "opponent")

        control = 0.0
        if state.field.tailwind_player_turns > 0:
            control += 15.0
        if state.field.tailwind_opponent_turns > 0:
            control -= 15.0
        if state.field.trick_room_turns > 0:
            control += (speed_opp - speed_player) * 0.02

        status_score = 0.0
        if state.opponent.status in ("burn", "poison", "paralysis"):
            status_score += 20.0
        if state.player.status in ("burn", "poison", "paralysis"):
            status_score -= 20.0

        return float(base + (p - 0.5) * 100 + control + status_score)

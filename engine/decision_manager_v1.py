from __future__ import annotations

from battle.action import ACTION_MOVE, ACTION_SWITCH
from engine.action_value_v1 import action_value
from engine.switch_value_v1 import switch_value


class DecisionManagerV1:
    @staticmethod
    def score_action(state, action, side_name: str = "player") -> float:
        kind = getattr(action, "action_type", None)
        if kind == ACTION_SWITCH:
            return switch_value(state, int(getattr(action, "switch_index", -1)), side_name)
        if kind == ACTION_MOVE:
            return action_value(state, action, side_name)
        return -100000.0

    @staticmethod
    def rank_actions(state, actions, side_name: str = "player"):
        scored = [(DecisionManagerV1.score_action(state, a, side_name), a) for a in actions]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    @staticmethod
    def choose_best(state, actions, side_name: str = "player"):
        ranked = DecisionManagerV1.rank_actions(state, actions, side_name)
        if not ranked:
            return None, -100000.0
        return ranked[0][1], float(ranked[0][0])

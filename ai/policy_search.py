from __future__ import annotations
from math import inf

from battle.action import Action, ACTION_MOVE, ACTION_SWITCH
from engine.turn_engine import TurnEngine
from engine.evaluation_engine import EvaluationEngine
from learning.policy import PolicyHead
from learning.value import ValueHead


class PolicySearch:
    @staticmethod
    def generate_actions(side, opponent=None):
        actions = []
        for move in getattr(side.active, "moves", []):
            actions.append(Action(ACTION_MOVE, move=move))
        for idx, _score in side.best_switch_candidates(opponent):
            actions.append(Action(ACTION_SWITCH, switch_index=idx))
        return actions

    @staticmethod
    def choose(state, depth=2):
        actions = PolicySearch.generate_actions(state.player_side, state.opponent)
        if not actions:
            return None, EvaluationEngine.evaluate(state)

        best_action = None
        best_score = -inf
        for action in actions:
            local = PolicyHead.score_action(state, action)
            value = ValueHead.estimate(state)

            # one-ply deterministic lookahead
            if getattr(action, "action_type", None) == ACTION_MOVE:
                from data.move_database import get_move
                mv = get_move(action.move)
                if mv and mv.category != "status":
                    # rough estimate against current opponent
                    from engine.damage_engine import calculate_damage
                    dmg = calculate_damage(state.player, state.opponent, action.move, state.field).avg_damage
                    local += dmg / max(1, state.opponent.current_hp) * 2.0
                elif mv and mv.name in ("protect", "recover", "tailwind"):
                    local += 0.5

            if depth <= 1:
                score = local + value * 2.0
            else:
                next_state = state.copy()
                opp_action = PolicySearch.generate_actions(state.opponent_side, state.player)[0] if PolicySearch.generate_actions(state.opponent_side, state.player) else None
                if opp_action is None:
                    score = local + EvaluationEngine.evaluate(next_state)
                else:
                    TurnEngine.execute(next_state, action, opp_action)
                    score = local + EvaluationEngine.evaluate(next_state)

            if score > best_score:
                best_score = score
                best_action = action

        return best_action, best_score

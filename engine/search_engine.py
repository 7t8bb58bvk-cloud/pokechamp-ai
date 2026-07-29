from __future__ import annotations
from math import inf
from battle.action import Action, ACTION_MOVE, ACTION_SWITCH
from engine.turn_engine import TurnEngine
from engine.evaluation_engine import EvaluationEngine
from engine.opening_book import OpeningBook


class SearchEngine:
    @staticmethod
    def generate_actions(side, opponent=None):
        actions = []
        for move in getattr(side.active, "moves", []):
            actions.append(Action(ACTION_MOVE, move=move))
        for idx, _score in side.best_switch_candidates(opponent):
            actions.append(Action(ACTION_SWITCH, switch_index=idx))
        return actions

    @staticmethod
    def _immediate_bonus(state, action):
        from engine.damage_engine import calculate_damage
        if action.action_type != ACTION_MOVE:
            return 0.0
        dmg = calculate_damage(state.player, state.opponent, action.move, state.field).avg_damage
        if dmg >= state.opponent.current_hp:
            return 10_000.0
        if action.move in ("protect", "recover", "tailwind"):
            return 50.0
        if action.move in ("swords-dance", "dragon-dance", "calm-mind"):
            return 25.0
        return 0.0

    @staticmethod
    def _score_after_turn(state, player_action, depth: int):
        opp_actions = SearchEngine.generate_actions(state.opponent_side, state.player)
        if not opp_actions:
            new_state = state.copy()
            opp_move = getattr(state.opponent, "moves", [None])[0]
            TurnEngine.execute(new_state, player_action, Action(ACTION_MOVE, move=opp_move))
            return EvaluationEngine.evaluate(new_state)

        worst = inf
        for opp_action in opp_actions:
            new_state = state.copy()
            TurnEngine.execute(new_state, player_action, opp_action)
            if new_state.battle_over() or depth <= 1:
                score = EvaluationEngine.evaluate(new_state)
            else:
                _, score = SearchEngine.choose_best_action(new_state, depth=depth - 1)
            worst = min(worst, score)
        return worst

    @staticmethod
    def choose_best_action(state, depth=2):
        opening = OpeningBook.choose(state)
        actions = SearchEngine.generate_actions(state.player_side, state.opponent)
        if not actions:
            return None, EvaluationEngine.evaluate(state)

        best_action = None
        best_score = -inf
        for action in actions:
            score = SearchEngine._score_after_turn(state, action, max(1, depth))
            score += SearchEngine._immediate_bonus(state, action)
            if opening is not None and action.action_type == ACTION_MOVE and action.move == opening:
                score += 15.0
            if score > best_score:
                best_score = score
                best_action = action
        return best_action, best_score

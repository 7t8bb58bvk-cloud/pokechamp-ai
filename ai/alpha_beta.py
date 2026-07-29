from __future__ import annotations
from math import inf

from battle.action import Action, ACTION_MOVE, ACTION_SWITCH
from engine.turn_engine import TurnEngine
from engine.evaluation_engine import EvaluationEngine
from engine.opening_book import OpeningBook
from ai.transposition import TranspositionTable


class AlphaBetaSearch:
    def __init__(self):
        self.tt = TranspositionTable()

    @staticmethod
    def generate_actions(side, opponent=None):
        actions = []
        for move in getattr(side.active, "moves", []):
            actions.append(Action(ACTION_MOVE, move=move))
        for idx, _score in side.best_switch_candidates(opponent):
            actions.append(Action(ACTION_SWITCH, switch_index=idx))
        return actions

    def _order_actions(self, state, actions):
        opening = OpeningBook.choose(state)
        def score(a):
            base = 0.0
            if a.action_type == ACTION_SWITCH:
                base += 1.0
            if a.action_type == ACTION_MOVE and a.move == opening:
                base += 2.5
            if a.action_type == ACTION_MOVE and a.move in ("protect", "recover", "tailwind"):
                base += 1.5
            if a.action_type == ACTION_MOVE and a.move in ("earthquake", "surf", "thunderbolt", "moonblast", "shadow-ball", "flamethrower"):
                base += 2.0
            return base
        return sorted(actions, key=score, reverse=True)

    def _opponent_response(self, state, depth):
        actions = self.generate_actions(state.opponent_side, state.player)
        if not actions:
            return None, EvaluationEngine.evaluate(state)
        best_action = None
        worst_score = inf
        for action in self._order_actions(state, actions):
            new_state = state.copy()
            player_move = getattr(state.player, "moves", [None])[0]
            TurnEngine.execute(new_state, Action(ACTION_MOVE, move=player_move), action)
            score = self.search(new_state, depth - 1, False)
            if score < worst_score:
                worst_score = score
                best_action = action
        return best_action, worst_score

    def search(self, state, depth: int, maximizing: bool = True):
        if state.battle_over() or depth <= 0:
            return EvaluationEngine.evaluate(state)

        cached = self.tt.get(state, depth)
        if cached is not None:
            return cached.score

        if maximizing:
            actions = self.generate_actions(state.player_side, state.opponent)
            if not actions:
                return EvaluationEngine.evaluate(state)
            best = -inf
            best_action = None
            for action in self._order_actions(state, actions):
                new_state = state.copy()
                opp_action, _ = self._opponent_response(new_state, depth)
                if opp_action is None:
                    opp_action = Action(ACTION_MOVE, move=getattr(new_state.opponent, "moves", [None])[0])
                TurnEngine.execute(new_state, action, opp_action)
                val = self.search(new_state, depth - 1, False)
                if val > best:
                    best = val
                    best_action = action
            self.tt.put(state, depth, best, "exact", best_action)
            return best
        else:
            # minimizing node: opponent response already handled in the maximizing path,
            # so this branch only evaluates the current state.
            score = EvaluationEngine.evaluate(state)
            self.tt.put(state, depth, score, "exact", None)
            return score

    def choose_action(self, state, depth: int = 2):
        opening = OpeningBook.choose(state)
        actions = self.generate_actions(state.player_side, state.opponent)
        if not actions:
            return None, EvaluationEngine.evaluate(state)

        if opening is not None:
            for a in actions:
                if a.action_type == ACTION_MOVE and a.move == opening:
                    return a, self.search(state, depth, True)

        best_action = None
        best_score = -inf
        for action in self._order_actions(state, actions):
            new_state = state.copy()
            opp_action, _ = self._opponent_response(new_state, depth)
            if opp_action is None:
                opp_action = Action(ACTION_MOVE, move=getattr(new_state.opponent, "moves", [None])[0])
            TurnEngine.execute(new_state, action, opp_action)
            val = self.search(new_state, depth - 1, False)
            if val > best_score:
                best_score = val
                best_action = action
        return best_action, best_score

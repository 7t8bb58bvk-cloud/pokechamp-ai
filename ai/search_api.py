from __future__ import annotations

from ai.alpha_beta import AlphaBetaSearch
from learning.puct import puct_choose_action
from engine.search_engine import SearchEngine
from engine.evaluation_engine import EvaluationEngine


class SearchAPI:
    def __init__(self):
        self.alpha_beta = AlphaBetaSearch()

    def choose(self, state, mode: str = "hybrid", depth: int = 2, iterations: int = 64):
        if mode == "alpha_beta":
            return self.alpha_beta.choose_action(state, depth=depth)
        if mode == "puct":
            action = puct_choose_action(state, iterations=iterations, depth=depth)
            return action, EvaluationEngine.evaluate(state)
        if mode == "minimax":
            return SearchEngine.choose_best_action(state, depth=depth)
        # hybrid default: alpha-beta first, fallback to minimax if needed
        action, score = self.alpha_beta.choose_action(state, depth=depth)
        if action is not None:
            return action, score
        return SearchEngine.choose_best_action(state, depth=depth)

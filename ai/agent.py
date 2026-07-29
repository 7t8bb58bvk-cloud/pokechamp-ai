from __future__ import annotations

from engine.opening_book import OpeningBook
from engine.search_engine import SearchEngine
from learning.puct import puct_choose_action


class Agent:
    @staticmethod
    def choose_action(state, mode: str = "hybrid", depth: int = 2, iterations: int = 64):
        opening = OpeningBook.choose(state)
        if opening is not None:
            for action in SearchEngine.generate_actions(state.player_side, state.opponent):
                if getattr(action, "move", None) == opening:
                    return action, 9999.0

        if mode == "puct":
            action = puct_choose_action(state, iterations=iterations, depth=depth)
            return action, 0.0

        action, score = SearchEngine.choose_best_action(state, depth=depth)
        return action, score

from __future__ import annotations
import time

from battle.team_builder import TeamBuilder
from battle.battle_state import BattleState
from engine.search_engine import SearchEngine
from ai.alpha_beta import AlphaBetaSearch
from learning.puct import puct_choose_action


class Benchmark:
    @staticmethod
    def make_state():
        player_side = TeamBuilder.create(["garchomp", "rotom", "amoonguss"])
        opponent_side = TeamBuilder.create(["primarina", "incineroar", "flutter-mane"])
        return BattleState(player_side=player_side, opponent_side=opponent_side)

    @staticmethod
    def run_once(mode: str = "minimax", depth: int = 2, iterations: int = 64):
        state = Benchmark.make_state()
        t0 = time.perf_counter()
        if mode == "puct":
            action = puct_choose_action(state, iterations=iterations, depth=depth)
            score = 0.0
        elif mode == "alpha_beta":
            search = AlphaBetaSearch()
            action, score = search.choose_action(state, depth=depth)
        else:
            action, score = SearchEngine.choose_best_action(state, depth=depth)
        dt = time.perf_counter() - t0
        return {
            "mode": mode,
            "seconds": dt,
            "action": repr(action),
            "score": score,
        }

    @staticmethod
    def compare():
        rows = []
        for mode in ("minimax", "alpha_beta", "puct"):
            rows.append(Benchmark.run_once(mode=mode))
        return rows

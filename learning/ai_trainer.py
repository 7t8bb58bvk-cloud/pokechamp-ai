from __future__ import annotations
from learning.self_play import SelfPlay


class AITrainer:
    @staticmethod
    def train(player_side, opponent_side, games=10, depth=2):
        results = {"player": 0, "opponent": 0, "draw": 0, "turns": []}
        for i in range(games):
            battle = SelfPlay.play(player_side, opponent_side, depth=depth)
            results[battle["winner"]] += 1
            results["turns"].append(battle["turns"])
            print(f"{i+1}/{games} games finished | winner={battle['winner']} | turns={battle['turns']}")
        return results

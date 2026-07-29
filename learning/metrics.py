from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TrainingMetrics:
    games: int = 0
    player_wins: int = 0
    opponent_wins: int = 0
    draws: int = 0
    turns: list[int] = field(default_factory=list)

    def add(self, result):
        self.games += 1
        winner = result.get("winner", "draw")
        if winner == "player":
            self.player_wins += 1
        elif winner == "opponent":
            self.opponent_wins += 1
        else:
            self.draws += 1
        self.turns.append(int(result.get("turns", 0)))

    def summary(self):
        avg_turns = sum(self.turns) / max(1, len(self.turns))
        return {
            "games": self.games,
            "player_wins": self.player_wins,
            "opponent_wins": self.opponent_wins,
            "draws": self.draws,
            "avg_turns": avg_turns,
        }

from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class Side:
    team: list
    active_index: int = 0
    side_conditions: dict[str, object] = field(default_factory=dict)

    @property
    def active(self):
        return self.team[self.active_index]

    def switch(self, index: int) -> bool:
        if index == self.active_index:
            return False
        if index < 0 or index >= len(self.team):
            return False
        if getattr(self.team[index], "fainted", False):
            return False
        self.active_index = index
        return True

    def alive_count(self) -> int:
        return sum(1 for p in self.team if not getattr(p, "fainted", False))

    def best_switch_candidates(self, opponent=None):
        candidates = []
        for i, p in enumerate(self.team):
            if i == self.active_index or getattr(p, "fainted", False):
                continue
            score = (p.current_hp or 0) / max(1, p.max_hp or 1)
            if opponent is not None:
                for mv in getattr(p, "moves", []):
                    if mv in ("protect", "recover"):
                        score += 0.02
            candidates.append((i, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:2]

    def clone(self):
        return deepcopy(self)

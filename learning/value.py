from __future__ import annotations
from engine.win_probability import WinProbability

class ValueHead:
    @staticmethod
    def estimate(state):
        return WinProbability.estimate_from_state(state)

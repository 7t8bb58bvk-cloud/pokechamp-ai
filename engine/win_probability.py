from __future__ import annotations
import math


class WinProbability:
    @staticmethod
    def logistic(score: float) -> float:
        return 1.0 / (1.0 + math.exp(-score / 250.0))

    @staticmethod
    def estimate_from_state(state) -> float:
        from engine.evaluation_engine import EvaluationEngine
        score = EvaluationEngine.evaluate(state)
        return WinProbability.logistic(score)

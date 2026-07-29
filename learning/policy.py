from __future__ import annotations

class PolicyHead:
    @staticmethod
    def score_action(state, action):
        score = 0.0
        if getattr(action, "action_type", None) == "switch":
            score += 0.5
        move = str(getattr(action, "move", "")).lower()
        if move in ("protect", "recover", "tailwind"):
            score += 1.0
        if move in ("swords-dance", "dragon-dance", "calm-mind"):
            score += 0.8
        if move in ("earthquake", "surf", "thunderbolt", "moonblast", "shadow-ball", "flamethrower"):
            score += 0.7
        return score

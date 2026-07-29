from __future__ import annotations
from data.move_database import get_move
from engine.damage_engine import calculate_damage


class OpponentModel:
    @staticmethod
    def predict_best_move(attacker, defender, field=None):
        best_move = None
        best_score = -1
        for move_name in attacker.moves:
            mv = get_move(move_name)
            if mv is None:
                continue
            if mv.category == "status":
                score = 20 if mv.name in ("swords-dance", "dragon-dance", "tailwind", "recover") else 5
            else:
                dmg = calculate_damage(attacker, defender, mv.name, field).avg_damage
                score = float(dmg)
                if dmg >= defender.current_hp:
                    score += 1000
            if score > best_score:
                best_score = score
                best_move = mv.name
        return best_move

    @staticmethod
    def should_switch(attacker, defender):
        hp_ratio = attacker.current_hp / max(1, attacker.max_hp)
        if hp_ratio < 0.25:
            return True
        return False

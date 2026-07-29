from __future__ import annotations
from dataclasses import dataclass
from math import floor
from data.move_database import get_move
from data.type_chart import type_multiplier
from engine.stat_engine import get_modified_stat


@dataclass
class DamageEstimate:
    min_damage: int
    max_damage: int
    avg_damage: float


def stab(attacker, move_type: str) -> float:
    move_type = str(move_type).lower()
    return 1.5 if move_type in [str(t).lower() for t in attacker.types] else 1.0


def weather_modifier(move_type: str, field) -> float:
    move_type = str(move_type).lower()
    weather = getattr(field, "weather", None) if field else None
    if weather == "sun" and move_type == "fire":
        return 1.5
    if weather == "sun" and move_type == "water":
        return 0.5
    if weather == "rain" and move_type == "water":
        return 1.5
    if weather == "rain" and move_type == "fire":
        return 0.5
    return 1.0


def calculate_damage(attacker, defender, move_name: str, field=None) -> DamageEstimate:
    move = get_move(move_name)
    if move is None:
        raise ValueError(f"unknown move: {move_name}")
    if move.category == "status":
        return DamageEstimate(0, 0, 0.0)

    if defender.volatile_status.get("protect"):
        return DamageEstimate(0, 0, 0.0)

    atk_stat = get_modified_stat(attacker, "spa" if move.category == "special" else "atk")
    def_stat = get_modified_stat(defender, "spd" if move.category == "special" else "def")

    level_factor = (2 * attacker.level / 5) + 2
    base = (((level_factor * move.power * atk_stat / max(1, def_stat)) / 50) + 2)

    modifier = (
        stab(attacker, move.type)
        * type_multiplier(move.type, defender.types)
        * weather_modifier(move.type, field)
    )

    if attacker.status == "burn" and move.category == "physical" and attacker.ability != "guts":
        modifier *= 0.5

    min_damage = max(1, floor(base * modifier * 0.85))
    max_damage = max(min_damage, floor(base * modifier))
    avg_damage = (min_damage + max_damage) / 2
    return DamageEstimate(min_damage, max_damage, avg_damage)

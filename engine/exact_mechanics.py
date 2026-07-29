from __future__ import annotations
from dataclasses import dataclass
from math import floor

from data.move_database import get_move
from data.type_chart import type_multiplier
from engine.stat_engine import get_modified_stat


@dataclass(frozen=True)
class DamageProfile:
    move: str
    min_damage: int
    max_damage: int
    avg_damage: float
    rolls: tuple[int, ...]
    accuracy: float
    ko_chance: float


@dataclass(frozen=True)
class MechanicsConfig:
    crit_multiplier: float = 1.5
    burn_multiplier: float = 0.5
    weather_boost: float = 1.5
    weather_drop: float = 0.5
    protect_multiplier: float = 0.0


CONFIG = MechanicsConfig()


def stab(attacker, move_type: str) -> float:
    move_type = str(move_type).lower()
    return 1.5 if move_type in [str(t).lower() for t in getattr(attacker, "types", ())] else 1.0


def accuracy_multiplier(attacker, defender, move) -> float:
    if move.category == "status":
        return 1.0
    acc = getattr(move, "accuracy", 100) or 100
    return max(0.0, min(1.0, acc / 100.0))


def crit_chance(attacker, move) -> float:
    return 0.0625


def crit_multiplier(attacker, defender, move) -> float:
    return CONFIG.crit_multiplier


def weather_modifier(move_type: str, field) -> float:
    move_type = str(move_type).lower()
    weather = getattr(field, "weather", None) if field else None
    if weather == "sun" and move_type == "fire":
        return CONFIG.weather_boost
    if weather == "sun" and move_type == "water":
        return CONFIG.weather_drop
    if weather == "rain" and move_type == "water":
        return CONFIG.weather_boost
    if weather == "rain" and move_type == "fire":
        return CONFIG.weather_drop
    return 1.0


def base_damage(attacker, defender, move, field=None, crit: bool = False) -> float:
    if move.category == "status":
        return 0.0

    atk_stat = get_modified_stat(attacker, "spa" if move.category == "special" else "atk")
    def_stat = get_modified_stat(defender, "spd" if move.category == "special" else "def")

    level_factor = (2 * attacker.level / 5) + 2
    base = (((level_factor * move.power * atk_stat / max(1, def_stat)) / 50) + 2)

    modifier = (
        stab(attacker, move.type)
        * type_multiplier(move.type, getattr(defender, "types", ()))
        * weather_modifier(move.type, field)
    )

    if getattr(attacker, "status", None) == "burn" and move.category == "physical" and getattr(attacker, "ability", "") != "guts":
        modifier *= CONFIG.burn_multiplier

    if crit:
        modifier *= crit_multiplier(attacker, defender, move)

    if getattr(defender, "volatile_status", {}).get("protect"):
        modifier *= CONFIG.protect_multiplier

    return base * modifier


def damage_rolls(attacker, defender, move_name: str, field=None) -> DamageProfile:
    move = get_move(move_name)
    if move is None:
        # Unknown move fallback: do not crash the notebook.
        return DamageProfile(
            move=move_name,
            min_damage=0,
            max_damage=0,
            avg_damage=0.0,
            rolls=(0,) * 16,
            accuracy=0.0,
            ko_chance=0.0,
        )

    if move.category == "status":
        return DamageProfile(
            move=move.name,
            min_damage=0,
            max_damage=0,
            avg_damage=0.0,
            rolls=(0,) * 16,
            accuracy=1.0,
            ko_chance=0.0,
        )

    acc = accuracy_multiplier(attacker, defender, move)
    raw = base_damage(attacker, defender, move, field=field, crit=False)

    rolls = []
    hp = max(1, int(getattr(defender, "current_hp", 1) or 1))
    for i in range(16):
        roll = 0.85 + (i / 100.0)
        dmg = max(1, floor(raw * roll))
        rolls.append(dmg)

    min_damage = min(rolls)
    max_damage = max(rolls)
    avg_damage = sum(rolls) / len(rolls)
    ko_chance = sum(1 for d in rolls if d >= hp) / len(rolls) * acc

    return DamageProfile(
        move=move.name,
        min_damage=min_damage,
        max_damage=max_damage,
        avg_damage=avg_damage,
        rolls=tuple(rolls),
        accuracy=acc,
        ko_chance=ko_chance,
    )


def calculate_damage(attacker, defender, move_name: str, field=None):
    return damage_rolls(attacker, defender, move_name, field=field)

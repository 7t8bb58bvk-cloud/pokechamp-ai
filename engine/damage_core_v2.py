from __future__ import annotations

from dataclasses import dataclass
from math import floor

from data.move_database import get_move
from data.type_chart import type_multiplier
from engine.stat_engine import get_modified_stat


@dataclass(frozen=True)
class DamageProfileV2:
    move: str
    min_damage: int
    max_damage: int
    avg_damage: float
    rolls: tuple[int, ...]
    ko_chance: float
    accuracy: float


def _stab(attacker, move_type: str) -> float:
    types = [str(t).lower() for t in getattr(attacker, "types", ())]
    return 1.5 if str(move_type).lower() in types else 1.0


def _weather_modifier(move_type: str, field) -> float:
    weather = getattr(field, "weather", None) if field else None
    move_type = str(move_type).lower()

    if weather == "sun":
        if move_type == "fire":
            return 1.5
        if move_type == "water":
            return 0.5
    if weather == "rain":
        if move_type == "water":
            return 1.5
        if move_type == "fire":
            return 0.5

    return 1.0


def _burn_modifier(attacker, move) -> float:
    if getattr(attacker, "status", None) == "burn" and move.category == "physical" and getattr(attacker, "ability", "") != "guts":
        return 0.5
    return 1.0


def _item_modifier(attacker, move) -> float:
    item = str(getattr(attacker, "item", "")).lower()
    move_type = str(move.type).lower()

    if item == "choice-specs" and move.category == "special":
        return 1.5
    if item == "choice-band" and move.category == "physical":
        return 1.5
    if item == "life-orb":
        return 1.3
    if item == "miracle-seed" and move_type == "grass":
        return 1.2
    if item == "mystic-water" and move_type == "water":
        return 1.2
    if item == "magnet" and move_type == "electric":
        return 1.2
    if item == "charcoal" and move_type == "fire":
        return 1.2
    if item == "soft-sand" and move_type == "ground":
        return 1.2
    return 1.0


def _type_effectiveness(move_type: str, defender_types) -> float:
    return type_multiplier(move_type, defender_types)


def _accuracy(move) -> float:
    if move.category == "status":
        return 1.0
    acc = getattr(move, "accuracy", 100) or 100
    return max(0.0, min(1.0, acc / 100.0))


def _raw_damage(attacker, defender, move, field, crit: bool = False) -> float:
    if move.category == "status":
        return 0.0

    atk_stat = get_modified_stat(attacker, "spa" if move.category == "special" else "atk")
    def_stat = get_modified_stat(defender, "spd" if move.category == "special" else "def")

    level = getattr(attacker, "level", 50)
    level_factor = (2 * level / 5) + 2
    base = (((level_factor * move.power * atk_stat / max(1, def_stat)) / 50) + 2)

    modifier = 1.0
    modifier *= _stab(attacker, move.type)
    modifier *= _type_effectiveness(move.type, getattr(defender, "types", ()))
    modifier *= _weather_modifier(move.type, field)
    modifier *= _burn_modifier(attacker, move)
    modifier *= _item_modifier(attacker, move)

    if crit:
        modifier *= 1.5

    if getattr(defender, "volatile_status", {}).get("protect"):
        modifier *= 0.0

    if str(getattr(attacker, "item", "")).lower() == "expert-belt":
        eff = _type_effectiveness(move.type, getattr(defender, "types", ()))
        if eff > 1.0:
            modifier *= 1.2

    return base * modifier


def damage_rolls(attacker, defender, move_name: str, field=None) -> DamageProfileV2:
    move = get_move(move_name)
    if move is None:
        return DamageProfileV2(
            move=move_name,
            min_damage=0,
            max_damage=0,
            avg_damage=0.0,
            rolls=(0,) * 16,
            ko_chance=0.0,
            accuracy=0.0,
        )

    if move.category == "status":
        return DamageProfileV2(
            move=move.name,
            min_damage=0,
            max_damage=0,
            avg_damage=0.0,
            rolls=(0,) * 16,
            ko_chance=0.0,
            accuracy=1.0,
        )

    acc = _accuracy(move)
    raw = _raw_damage(attacker, defender, move, field, crit=False)

    rolls = []
    hp = max(1, int(getattr(defender, "current_hp", 1) or 1))
    for i in range(16):
        roll = 0.85 + (i / 100.0)
        dmg = max(1, floor(raw * roll))
        rolls.append(dmg)

    min_damage = min(rolls)
    max_damage = max(rolls)
    avg_damage = sum(rolls) / len(rolls)
    ko_chance = (sum(1 for d in rolls if d >= hp) / 16.0) * acc

    return DamageProfileV2(
        move=move.name,
        min_damage=min_damage,
        max_damage=max_damage,
        avg_damage=avg_damage,
        rolls=tuple(rolls),
        ko_chance=ko_chance,
        accuracy=acc,
    )

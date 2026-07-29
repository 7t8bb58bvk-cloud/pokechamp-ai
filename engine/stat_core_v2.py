from __future__ import annotations

from math import floor

NATURES = {
    "adamant": {"atk": 1.1, "spa": 0.9},
    "modest": {"spa": 1.1, "atk": 0.9},
    "jolly": {"spe": 1.1, "spa": 0.9},
    "timid": {"spe": 1.1, "atk": 0.9},
    "bold": {"def": 1.1, "atk": 0.9},
    "calm": {"spd": 1.1, "atk": 0.9},
    "careful": {"spd": 1.1, "spa": 0.9},
    "naive": {"spe": 1.1, "spd": 0.9},
    "serious": {},
    "hardy": {},
    "docile": {},
    "bashful": {},
    "quirky": {},
}

def nature_multiplier(nature: str, stat: str) -> float:
    return NATURES.get(str(nature).lower(), {}).get(stat, 1.0)

def stage_multiplier(stage: int) -> float:
    stage = int(stage)
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 - stage)

def calculate_hp(base: int, iv: int = 31, ev: int = 0, level: int = 50) -> int:
    return floor(((2 * base + iv + ev // 4) * level) / 100) + level + 10

def calculate_other_stat(base: int, iv: int = 31, ev: int = 0, level: int = 50, nature: float = 1.0) -> int:
    return floor(((((2 * base + iv + ev // 4) * level) / 100) + 5) * nature)

def get_modified_stat(pokemon, stat: str) -> int:
    if stat == "hp":
        return int(getattr(pokemon, "max_hp", 0) or calculate_hp(
            pokemon.base_stats["hp"],
            pokemon.ivs.get("hp", 31),
            pokemon.evs.get("hp", 0),
            pokemon.level,
        ))

    base = pokemon.base_stats[stat]
    iv = pokemon.ivs.get(stat, 31)
    ev = pokemon.evs.get(stat, 0)
    nature = nature_multiplier(getattr(pokemon, "nature", "serious"), stat)
    raw = calculate_other_stat(base, iv, ev, pokemon.level, nature)
    stage = getattr(pokemon, "boosts", {}).get(stat, 0)
    return max(1, int(raw * stage_multiplier(stage)))

def calculate_speed(pokemon, field=None, side_name: str = "player") -> int:
    speed = get_modified_stat(pokemon, "spe")

    status = getattr(pokemon, "status", None)
    ability = str(getattr(pokemon, "ability", "")).lower()
    item = str(getattr(pokemon, "item", "")).lower()

    if status == "paralysis" and ability != "quick-feet":
        speed = int(speed * 0.5)

    if item == "choice-scarf":
        speed = int(speed * 1.5)

    if item == "iron-ball":
        speed = int(speed * 0.5)

    weather = getattr(field, "weather", None) if field else None
    terrain = getattr(field, "terrain", None) if field else None

    if weather == "sun" and ability == "chlorophyll":
        speed *= 2
    elif weather == "rain" and ability == "swift-swim":
        speed *= 2
    elif weather == "sand" and ability == "sand-rush":
        speed *= 2
    elif weather == "snow" and ability == "slush-rush":
        speed *= 2
    elif terrain == "electric" and ability == "surge-surfer":
        speed *= 2
    elif status == "paralysis" and ability == "quick-feet":
        speed = int(speed * 1.5)

    if field is not None:
        if side_name == "player" and getattr(field, "tailwind_player_turns", 0) > 0:
            speed *= 2
        if side_name == "opponent" and getattr(field, "tailwind_opponent_turns", 0) > 0:
            speed *= 2

    return max(1, int(speed))

def effective_speed(pokemon, field=None, side_name: str = "player") -> int:
    speed = calculate_speed(pokemon, field, side_name)
    if field is not None and getattr(field, "trick_room_turns", 0) > 0:
        return -speed
    return speed

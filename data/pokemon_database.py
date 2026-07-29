from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PokemonTemplate:
    name: str
    types: tuple[str, ...]
    base_stats: dict[str, int]
    moves: tuple[str, ...]
    ability: str = "none"
    item: str = ""
    nature: str = "serious"
    level: int = 50
    tera_type: str | None = None


POKEMON_DATABASE: dict[str, PokemonTemplate] = {
    "garchomp": PokemonTemplate(
        "garchomp", ("dragon", "ground"),
        {"hp": 108, "atk": 130, "def": 95, "spa": 80, "spd": 85, "spe": 102},
        ("earthquake", "dragon-claw", "swords-dance", "protect"),
        ability="rough-skin", item="leftovers", nature="jolly",
    ),
    "rotom": PokemonTemplate(
        "rotom", ("electric", "ghost"),
        {"hp": 50, "atk": 65, "def": 107, "spa": 105, "spd": 107, "spe": 86},
        ("thunderbolt", "shadow-ball", "will-o-wisp", "protect"),
        ability="levitate", item="sitrus-berry", nature="timid",
    ),
    "primarina": PokemonTemplate(
        "primarina", ("water", "fairy"),
        {"hp": 80, "atk": 74, "def": 74, "spa": 126, "spd": 116, "spe": 60},
        ("surf", "moonblast", "ice-beam", "protect"),
        ability="torrent", item="leftovers", nature="modest",
    ),
    "dragonite": PokemonTemplate(
        "dragonite", ("dragon", "flying"),
        {"hp": 91, "atk": 134, "def": 95, "spa": 100, "spd": 100, "spe": 80},
        ("dragon-claw", "earthquake", "dragon-dance", "protect"),
        ability="multiscale", item="lum-berry", nature="adamant",
    ),
    "incineroar": PokemonTemplate(
        "incineroar", ("fire", "dark"),
        {"hp": 95, "atk": 115, "def": 90, "spa": 80, "spd": 90, "spe": 60},
        ("flamethrower", "knock-off", "tailwind", "protect"),
        ability="intimidate", item="sitrus-berry", nature="careful",
    ),
    "amoonguss": PokemonTemplate(
        "amoonguss", ("grass", "poison"),
        {"hp": 114, "atk": 85, "def": 70, "spa": 85, "spd": 80, "spe": 30},
        ("sludge-bomb", "protect", "recover", "will-o-wisp"),
        ability="regenerator", item="black-sludge", nature="bold",
    ),
    "gholdengo": PokemonTemplate(
        "gholdengo", ("steel", "ghost"),
        {"hp": 87, "atk": 60, "def": 95, "spa": 133, "spd": 91, "spe": 84},
        ("shadow-ball", "make-it-rain", "recover", "protect"),
        ability="good-as-gold", item="leftovers", nature="modest",
    ),
    "flutter-mane": PokemonTemplate(
        "flutter-mane", ("ghost", "fairy"),
        {"hp": 55, "atk": 55, "def": 55, "spa": 135, "spd": 135, "spe": 135},
        ("moonblast", "shadow-ball", "protect", "calm-mind"),
        ability="protosynthesis", item="booster-energy", nature="timid",
    ),
}


def get_template(name: str) -> PokemonTemplate | None:
    return POKEMON_DATABASE.get(str(name).strip().lower().replace(" ", "-"))

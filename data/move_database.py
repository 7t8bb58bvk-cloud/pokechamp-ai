from __future__ import annotations
from dataclasses import dataclass


def to_id(text: str) -> str:
    return str(text).strip().lower().replace(" ", "").replace("_", "-")


@dataclass(frozen=True)
class Move:
    name: str
    type: str
    category: str
    power: int = 0
    accuracy: int = 100
    priority: int = 0
    pp: int = 10


MOVE_DATABASE: dict[str, Move] = {
    "tackle": Move("tackle", "normal", "physical", 40),
    "quick-attack": Move("quick-attack", "normal", "physical", 40, priority=1),
    "flamethrower": Move("flamethrower", "fire", "special", 90),
    "fire-blast": Move("fire-blast", "fire", "special", 110, 85),
    "surf": Move("surf", "water", "special", 90),
    "hydro-pump": Move("hydro-pump", "water", "special", 110, 80),
    "thunderbolt": Move("thunderbolt", "electric", "special", 90),
    "earthquake": Move("earthquake", "ground", "physical", 100),
    "leaf-blade": Move("leaf-blade", "grass", "physical", 90),
    "ice-beam": Move("ice-beam", "ice", "special", 90),
    "dragon-claw": Move("dragon-claw", "dragon", "physical", 80),
    "shadow-ball": Move("shadow-ball", "ghost", "special", 80),
    "sludge-bomb": Move("sludge-bomb", "poison", "special", 90),
    "iron-head": Move("iron-head", "steel", "physical", 80),
    "body-press": Move("body-press", "fighting", "physical", 80),
    "protect": Move("protect", "normal", "status", 0, priority=4),
    "recover": Move("recover", "normal", "status", 0),
    "swords-dance": Move("swords-dance", "normal", "status", 0),
    "dragon-dance": Move("dragon-dance", "dragon", "status", 0),
    "calm-mind": Move("calm-mind", "psychic", "status", 0),
    "tailwind": Move("tailwind", "flying", "status", 0),
    "will-o-wisp": Move("will-o-wisp", "fire", "status", 0, accuracy=85),
    "moonblast": Move("moonblast", "fairy", "special", 95),
    "make-it-rain": Move("make-it-rain", "steel", "special", 120),
    "knock-off": Move("knock-off", "dark", "physical", 65),
}


def get_move(name: str) -> Move | None:
    key = to_id(name)
    return MOVE_DATABASE.get(key)


def all_moves() -> list[Move]:
    return list(MOVE_DATABASE.values())

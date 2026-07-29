from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy

STATS = ("hp", "atk", "def", "spa", "spd", "spe")


def default_ivs():
    return {s: 31 for s in STATS}


def default_evs():
    return {s: 0 for s in STATS}


def default_boosts():
    return {s: 0 for s in ("atk", "def", "spa", "spd", "spe", "accuracy", "evasion")}


@dataclass
class Pokemon:
    name: str
    types: tuple[str, ...]
    base_stats: dict[str, int]
    moves: list[str]
    level: int = 50
    ability: str = "none"
    item: str = ""
    nature: str = "serious"
    tera_type: str | None = None
    ivs: dict[str, int] = field(default_factory=default_ivs)
    evs: dict[str, int] = field(default_factory=default_evs)
    max_hp: int | None = None
    current_hp: int | None = None
    status: str | None = None
    boosts: dict[str, int] = field(default_factory=default_boosts)
    volatile_status: dict[str, object] = field(default_factory=dict)

    def clone(self) -> "Pokemon":
        return deepcopy(self)

    @property
    def fainted(self) -> bool:
        return (self.current_hp or 0) <= 0

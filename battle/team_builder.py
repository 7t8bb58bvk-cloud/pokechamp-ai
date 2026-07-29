from __future__ import annotations
from battle.pokemon import Pokemon
from battle.side import Side
from data.pokemon_database import get_template


class TeamBuilder:
    @staticmethod
    def create(team_names: list[str]) -> Side:
        team = []
        for name in team_names:
            t = get_template(name)
            if t is None:
                raise ValueError(f"unknown pokemon: {name}")
            p = Pokemon(
                name=t.name,
                types=t.types,
                base_stats=t.base_stats,
                moves=list(t.moves),
                level=t.level,
                ability=t.ability,
                item=t.item,
                nature=t.nature,
                tera_type=t.tera_type,
            )
            team.append(p)

        from engine.stat_engine import calculate_hp
        for p in team:
            p.max_hp = calculate_hp(p.base_stats["hp"], p.ivs["hp"], p.evs["hp"], p.level)
            p.current_hp = p.max_hp
        return Side(team=team)

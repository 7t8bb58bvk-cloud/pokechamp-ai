from __future__ import annotations

from battle.action import ACTION_MOVE, ACTION_SWITCH
from data.move_database import get_move
from engine.exact_mechanics import damage_rolls
from engine.stat_engine import effective_speed


class TurnEngineV1:
    @staticmethod
    def _first_move_name(pokemon):
        for m in getattr(pokemon, "moves", []) or []:
            if m:
                return m
        return None

    @staticmethod
    def _apply_status_move(state, user, move, side_name: str):
        name = str(move.name).lower()

        if name == "protect":
            user.volatile_status["protect"] = True
            user.volatile_status["protect_streak"] = int(user.volatile_status.get("protect_streak", 0)) + 1
        elif name == "swords-dance":
            user.boosts["atk"] = min(6, user.boosts.get("atk", 0) + 2)
            user.volatile_status["protect_streak"] = 0
        elif name == "dragon-dance":
            user.boosts["atk"] = min(6, user.boosts.get("atk", 0) + 1)
            user.boosts["spe"] = min(6, user.boosts.get("spe", 0) + 1)
            user.volatile_status["protect_streak"] = 0
        elif name == "calm-mind":
            user.boosts["spa"] = min(6, user.boosts.get("spa", 0) + 1)
            user.boosts["spd"] = min(6, user.boosts.get("spd", 0) + 1)
            user.volatile_status["protect_streak"] = 0
        elif name == "tailwind":
            if side_name == "player":
                state.field.tailwind_player_turns = 4
            else:
                state.field.tailwind_opponent_turns = 4
            user.volatile_status["protect_streak"] = 0
        elif name == "recover":
            user.current_hp = min(user.max_hp, user.current_hp + max(1, user.max_hp // 2))
            user.volatile_status["protect_streak"] = 0
        elif name == "will-o-wisp":
            target = state.opponent if side_name == "player" else state.player
            if getattr(target, "status", None) is None:
                target.status = "burn"
                state.log.append(f"{target.name} was burned")
            user.volatile_status["protect_streak"] = 0
        else:
            user.volatile_status["protect_streak"] = 0

        state.log.append(f"{user.name} used {move.name}")

    @staticmethod
    def _attack(state, attacker, defender, move, side_name: str):
        if defender.volatile_status.get("protect") and move.category != "status":
            state.log.append(f"{defender.name} protected itself")
            return

        prof = damage_rolls(attacker, defender, move.name, state.field)
        dmg = max(1, int(prof.avg_damage))
        defender.current_hp = max(0, defender.current_hp - dmg)
        state.log.append(f"{attacker.name} used {move.name} for {dmg} damage")
        if defender.current_hp == 0:
            state.log.append(f"{defender.name} fainted")

    @staticmethod
    def _end_of_turn(state):
        for pokemon in (state.player, state.opponent):
            if pokemon.current_hp <= 0:
                continue
            if pokemon.status == "burn":
                dmg = max(1, pokemon.max_hp // 16)
                pokemon.current_hp = max(0, pokemon.current_hp - dmg)
                state.log.append(f"{pokemon.name} was hurt by burn for {dmg}")
            elif pokemon.status == "poison":
                dmg = max(1, pokemon.max_hp // 8)
                pokemon.current_hp = max(0, pokemon.current_hp - dmg)
                state.log.append(f"{pokemon.name} was hurt by poison for {dmg}")

        if state.field.tailwind_player_turns > 0:
            state.field.tailwind_player_turns -= 1
        if state.field.tailwind_opponent_turns > 0:
            state.field.tailwind_opponent_turns -= 1
        if state.field.trick_room_turns > 0:
            state.field.trick_room_turns -= 1

        state.player.volatile_status.pop("protect", None)
        state.opponent.volatile_status.pop("protect", None)

    @staticmethod
    def execute(state, player_action, opponent_action):
        if player_action.action_type == ACTION_SWITCH:
            state.player_side.switch(player_action.switch_index)
            state.log.append(f"Player switched to {state.player.name}")
        if opponent_action.action_type == ACTION_SWITCH:
            state.opponent_side.switch(opponent_action.switch_index)
            state.log.append(f"Opponent switched to {state.opponent.name}")

        ordered = [
            ("player", player_action, state.player_side.active, state.opponent_side.active),
            ("opponent", opponent_action, state.opponent_side.active, state.player_side.active),
        ]

        def key(item):
            side_name, action, user, _target = item
            if action.action_type != ACTION_MOVE:
                return (-999, -999)
            move = get_move(action.move)
            prio = move.priority if move else 0
            spd = effective_speed(user, state.field, side_name)
            return (prio, spd)

        ordered.sort(key=key, reverse=True)

        for side_name, action, user, target in ordered:
            if state.battle_over():
                break
            if action.action_type != ACTION_MOVE:
                continue
            move = get_move(action.move)
            if move is None:
                continue
            if move.category == "status":
                TurnEngineV1._apply_status_move(state, user, move, side_name)
            else:
                TurnEngineV1._attack(state, user, target, move, side_name)

        TurnEngineV1._end_of_turn(state)
        state.next_turn()
        return state.log

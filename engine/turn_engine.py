from __future__ import annotations
from battle.action import ACTION_MOVE, ACTION_SWITCH
from data.move_database import get_move
from engine.damage_engine import calculate_damage


class TurnEngine:
    @staticmethod
    def _apply_status_move(state, user, move, user_side_name: str):
        name = move.name
        if name == "protect":
            user.volatile_status["protect"] = True
        elif name == "swords-dance":
            user.boosts["atk"] = min(6, user.boosts.get("atk", 0) + 2)
        elif name == "dragon-dance":
            user.boosts["atk"] = min(6, user.boosts.get("atk", 0) + 1)
            user.boosts["spe"] = min(6, user.boosts.get("spe", 0) + 1)
        elif name == "calm-mind":
            user.boosts["spa"] = min(6, user.boosts.get("spa", 0) + 1)
            user.boosts["spd"] = min(6, user.boosts.get("spd", 0) + 1)
        elif name == "tailwind":
            if user_side_name == "player":
                state.field.tailwind_player_turns = 4
            else:
                state.field.tailwind_opponent_turns = 4
        elif name == "recover":
            heal = max(1, user.max_hp // 2)
            user.current_hp = min(user.max_hp, user.current_hp + heal)
        state.log.append(f"{user.name} used {move.name}")

    @staticmethod
    def _attack(state, attacker, defender, move, attacker_side_name: str):
        if defender.volatile_status.get("protect") and move.category != "status":
            state.log.append(f"{defender.name} protected itself")
            return

        dmg = calculate_damage(attacker, defender, move.name, state.field).avg_damage
        dmg = max(1, int(dmg))
        defender.current_hp = max(0, defender.current_hp - dmg)
        state.log.append(f"{attacker.name} used {move.name} for {dmg} damage")

        if defender.current_hp == 0:
            state.log.append(f"{defender.name} fainted")

    @staticmethod
    def execute(state, player_action, opponent_action):
        if player_action.action_type == ACTION_SWITCH:
            state.player_side.switch(player_action.switch_index)
            state.log.append(f"Player switched to {state.player.name}")
        if opponent_action.action_type == ACTION_SWITCH:
            state.opponent_side.switch(opponent_action.switch_index)
            state.log.append(f"Opponent switched to {state.opponent.name}")

        actions = [
            ("player", player_action, state.player_side.active),
            ("opponent", opponent_action, state.opponent_side.active),
        ]

        def action_sort_key(item):
            side_name, action, user = item
            if action.action_type != ACTION_MOVE:
                return (-999, -999)
            move = get_move(action.move)
            prio = move.priority if move else 0
            from engine.stat_engine import effective_speed
            sp = effective_speed(user, state.field, side_name)
            return (prio, sp)

        actions = sorted(actions, key=action_sort_key, reverse=True)

        for side_name, action, user in actions:
            if state.battle_over():
                break
            if action.action_type == ACTION_MOVE:
                move = get_move(action.move)
                if move is None:
                    continue
                if move.category == "status":
                    TurnEngine._apply_status_move(state, user, move, side_name)
                else:
                    target = state.opponent_side.active if side_name == "player" else state.player_side.active
                    TurnEngine._attack(state, user, target, move, side_name)

        state.next_turn()
        return state.log

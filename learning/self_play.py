from __future__ import annotations
from battle.battle_state import BattleState
from battle.action import Action, ACTION_MOVE
from engine.search_engine import SearchEngine


class SelfPlay:
    @staticmethod
    def play(player_side, opponent_side, depth=2, max_turns=100):
        state = BattleState(player_side=player_side, opponent_side=opponent_side)
        history = []
        turns = 0

        while turns < max_turns and not state.battle_over():
            player_action, _ = SearchEngine.choose_best_action(state, depth=depth)
            if player_action is None:
                break

            swapped = BattleState(player_side=state.opponent_side, opponent_side=state.player_side)
            opp_action, _ = SearchEngine.choose_best_action(swapped, depth=depth)
            if opp_action is None:
                opp_action = Action(ACTION_MOVE, move=state.opponent.moves[0])

            history.extend(state.log)
            state.log = []
            from engine.turn_engine import TurnEngine
            TurnEngine.execute(state, player_action, opp_action)

            history.extend(state.log)
            state.log = []
            turns += 1

        return {
            "winner": state.winner(),
            "turns": turns,
            "history": history,
            "final_state": state,
        }

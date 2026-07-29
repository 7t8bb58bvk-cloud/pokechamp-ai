from __future__ import annotations

import time
from dataclasses import dataclass
from math import inf

from battle.action import Action, ACTION_MOVE, ACTION_SWITCH
from engine.exact_mechanics import damage_rolls
from engine.evaluation_core_v1 import EvaluationEngineV1
from engine.turn_core_v1 import TurnEngineV1


@dataclass
class TTEntryV2:
    depth: int
    score: float
    best_action: object | None


class TranspositionTableV2:
    def __init__(self):
        self._table: dict[tuple, TTEntryV2] = {}

    @staticmethod
    def _pack_pokemon(p) -> tuple:
        boosts = tuple(sorted((getattr(p, "boosts", {}) or {}).items()))
        vol = tuple(sorted((getattr(p, "volatile_status", {}) or {}).items()))
        return (
            getattr(p, "name", ""),
            getattr(p, "current_hp", None),
            getattr(p, "max_hp", None),
            getattr(p, "status", None),
            getattr(p, "ability", None),
            getattr(p, "item", None),
            getattr(p, "nature", None),
            boosts,
            vol,
        )

    @classmethod
    def key(cls, state) -> tuple:
        return (
            getattr(state, "turn", 0),
            getattr(state.player_side, "active_index", 0),
            getattr(state.opponent_side, "active_index", 0),
            cls._pack_pokemon(state.player),
            cls._pack_pokemon(state.opponent),
            tuple(cls._pack_pokemon(p) for p in getattr(state.player_side, "team", [])),
            tuple(cls._pack_pokemon(p) for p in getattr(state.opponent_side, "team", [])),
            getattr(state.field, "weather", None),
            getattr(state.field, "terrain", None),
            getattr(state.field, "trick_room_turns", 0),
            getattr(state.field, "tailwind_player_turns", 0),
            getattr(state.field, "tailwind_opponent_turns", 0),
        )

    def get(self, state, depth: int):
        entry = self._table.get(self.key(state))
        if entry is None:
            return None
        if entry.depth >= depth:
            return entry
        return None

    def put(self, state, depth: int, score: float, best_action=None):
        self._table[self.key(state)] = TTEntryV2(depth=depth, score=score, best_action=best_action)


class AlphaBetaSearchV2:
    def __init__(self):
        self.tt = TranspositionTableV2()
        self.nodes = 0

    @staticmethod
    def _first_move_name(pokemon):
        for m in getattr(pokemon, "moves", []) or []:
            if m:
                return m
        return None

    @staticmethod
    def _is_setup(move_name: str) -> bool:
        return str(move_name).lower() in ("swords-dance", "dragon-dance", "calm-mind", "tailwind")

    @staticmethod
    def _is_stall(move_name: str) -> bool:
        return str(move_name).lower() == "protect"

    @staticmethod
    def generate_actions(side, opponent=None):
        actions = []
        for move in getattr(side.active, "moves", []) or []:
            actions.append(Action(ACTION_MOVE, move=move))
        for idx, _score in side.best_switch_candidates(opponent):
            actions.append(Action(ACTION_SWITCH, switch_index=idx))
        return actions

    @staticmethod
    def _move_order_score(state, action, actor_side: str) -> float:
        if action.action_type == ACTION_SWITCH:
            hp = state.player.current_hp / max(1, state.player.max_hp) if actor_side == "player" else state.opponent.current_hp / max(1, state.opponent.max_hp)
            score = 10.0
            if hp < 0.35:
                score += 30.0
            return score

        attacker = state.player if actor_side == "player" else state.opponent
        defender = state.opponent if actor_side == "player" else state.player
        prof = damage_rolls(attacker, defender, action.move, state.field)
        score = float(prof.avg_damage) + float(prof.ko_chance) * 2000.0
        move = str(getattr(action, "move", "")).lower()
        if move in ("earthquake", "surf", "thunderbolt", "moonblast", "shadow-ball", "flamethrower", "ice-beam", "dragon-claw"):
            score += 35.0
        if move in ("swords-dance", "dragon-dance", "calm-mind"):
            score += 20.0
        if move == "protect":
            score -= 150.0
        if move == "recover":
            score += 15.0
        if move == "tailwind":
            score += 10.0
        return score

    @staticmethod
    def _leaf_eval(state) -> float:
        return float(EvaluationEngineV1.evaluate(state))

    def _player_actions(self, state):
        actions = self.generate_actions(state.player_side, state.opponent)
        return sorted(actions, key=lambda a: self._move_order_score(state, a, "player"), reverse=True) if actions else []

    def _opponent_actions(self, state):
        actions = self.generate_actions(state.opponent_side, state.player)
        if not actions:
            mv = self._first_move_name(state.opponent)
            return [Action(ACTION_MOVE, move=mv)] if mv else []
        return sorted(actions, key=lambda a: self._move_order_score(state, a, "opponent"), reverse=True)

    def _search(self, state, depth: int, alpha: float, beta: float) -> float:
        self.nodes += 1

        if state.battle_over() or depth <= 0:
            return self._leaf_eval(state)

        cached = self.tt.get(state, depth)
        if cached is not None:
            return cached.score

        player_actions = self._player_actions(state)
        opp_actions = self._opponent_actions(state)

        if not player_actions:
            return self._leaf_eval(state)
        if not opp_actions:
            return self._leaf_eval(state)

        best_score = -inf
        best_action = None

        for action in player_actions:
            if action.action_type == ACTION_MOVE:
                prof = damage_rolls(state.player, state.opponent, action.move, state.field)
                if prof.avg_damage >= state.opponent.current_hp:
                    self.tt.put(state, depth, 25000.0, action)
                    return 25000.0

            worst_reply = inf
            for opp_action in opp_actions[:4]:
                child = state.copy()
                TurnEngineV1.execute(child, action, opp_action)
                score = self._search(child, depth - 1, alpha, beta)
                if score < worst_reply:
                    worst_reply = score
                if worst_reply <= alpha:
                    break

            if worst_reply > best_score:
                best_score = worst_reply
                best_action = action
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        if best_action is None:
            best_score = self._leaf_eval(state)

        self.tt.put(state, depth, best_score, best_action)
        return best_score

    def choose_action(self, state, max_depth: int = 4, time_limit_sec: float | None = None):
        if state.battle_over():
            return None, self._leaf_eval(state)

        start = time.perf_counter()
        best_action = None
        best_score = -inf

        for depth in range(1, max_depth + 1):
            if time_limit_sec is not None and (time.perf_counter() - start) >= time_limit_sec:
                break

            actions = self._player_actions(state)
            if not actions:
                return None, self._leaf_eval(state)

            depth_best_action = None
            depth_best_score = -inf
            alpha = -inf
            beta = inf
            opp_actions = self._opponent_actions(state)
            if not opp_actions:
                return None, self._leaf_eval(state)

            for action in actions:
                if time_limit_sec is not None and (time.perf_counter() - start) >= time_limit_sec:
                    break

                if action.action_type == ACTION_MOVE:
                    prof = damage_rolls(state.player, state.opponent, action.move, state.field)
                    if prof.avg_damage >= state.opponent.current_hp:
                        return action, 25000.0

                worst = inf
                for opp_action in opp_actions[:4]:
                    child = state.copy()
                    TurnEngineV1.execute(child, action, opp_action)
                    score = self._search(child, depth - 1, alpha, beta)
                    if score < worst:
                        worst = score
                    if worst <= alpha:
                        break

                if worst > depth_best_score:
                    depth_best_score = worst
                    depth_best_action = action
                if depth_best_score > alpha:
                    alpha = depth_best_score
                if alpha >= beta:
                    break

            if depth_best_action is not None:
                best_action = depth_best_action
                best_score = depth_best_score

        return best_action, float(best_score)


SEARCHER = AlphaBetaSearchV2()


def choose_best_action(state, max_depth: int = 4, time_limit_sec: float | None = None):
    return SEARCHER.choose_action(state, max_depth=max_depth, time_limit_sec=time_limit_sec)

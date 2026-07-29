from __future__ import annotations

import time
from dataclasses import dataclass
from math import inf

from battle.action import Action, ACTION_MOVE, ACTION_SWITCH
from engine.exact_mechanics import damage_rolls
from engine.evaluation_engine import EvaluationEngine
from engine.turn_engine import TurnEngine


@dataclass
class TTEntry:
    depth: int
    score: float
    best_action: object | None


class TranspositionTable:
    def __init__(self):
        self._table: dict[tuple, TTEntry] = {}

    @staticmethod
    def _pack_pokemon(p) -> tuple:
        boosts = tuple(sorted((getattr(p, "boosts", {}) or {}).items()))
        vol = tuple(sorted((getattr(p, "volatile_status", {}) or {}).keys()))
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
        self._table[self.key(state)] = TTEntry(depth=depth, score=score, best_action=best_action)

    def __len__(self):
        return len(self._table)


class AlphaBetaSearchV1:
    def __init__(self):
        self.tt = TranspositionTable()

    @staticmethod
    def _first_move_name(pokemon):
        moves = getattr(pokemon, "moves", []) or []
        for m in moves:
            if m:
                return m
        return None

    @staticmethod
    def generate_actions(side, opponent=None):
        actions = []
        for move in getattr(side.active, "moves", []) or []:
            actions.append(Action(ACTION_MOVE, move=move))
        for idx, _score in side.best_switch_candidates(opponent):
            actions.append(Action(ACTION_SWITCH, switch_index=idx))
        return actions

    @staticmethod
    def _order_actions(state, actions, actor_side_name: str):
        def score_action(action):
            if action.action_type == ACTION_SWITCH:
                score = 2.0
                if actor_side_name == "player" and state.player.current_hp / max(1, state.player.max_hp) < 0.35:
                    score += 25.0
                if actor_side_name == "opponent" and state.opponent.current_hp / max(1, state.opponent.max_hp) < 0.35:
                    score += 25.0
                return score

            prof = damage_rolls(state.player if actor_side_name == "player" else state.opponent,
                                state.opponent if actor_side_name == "player" else state.player,
                                action.move,
                                state.field)
            score = float(prof.avg_damage) + float(prof.ko_chance) * 1000.0

            move = str(getattr(action, "move", "")).lower()
            if move in ("earthquake", "surf", "thunderbolt", "moonblast", "shadow-ball", "flamethrower", "ice-beam", "dragon-claw"):
                score += 25.0
            if move in ("swords-dance", "dragon-dance", "calm-mind"):
                score += 20.0
            if move == "protect":
                score -= 80.0
            if move == "recover":
                score += 10.0
            if move == "tailwind":
                score += 12.0
            return score

        return sorted(actions, key=score_action, reverse=True)

    def _terminal_score(self, state) -> float:
        return float(EvaluationEngine.evaluate(state))

    def _search_turn(self, state, depth: int, alpha: float, beta: float) -> float:
        if depth <= 0 or state.battle_over():
            return self._terminal_score(state)

        cached = self.tt.get(state, depth)
        if cached is not None:
            return cached.score

        player_actions = self._order_actions(state, self.generate_actions(state.player_side, state.opponent), "player")
        opp_actions = self._order_actions(state, self.generate_actions(state.opponent_side, state.player), "opponent")

        if not player_actions:
            return self._terminal_score(state)
        if not opp_actions:
            opp_actions = [Action(ACTION_MOVE, move=self._first_move_name(state.opponent))]

        best_score = -inf
        best_action = None

        for action in player_actions:
            if best_score >= beta:
                break

            worst_reply = inf

            for opp_action in opp_actions[:4]:
                child = state.copy()
                TurnEngine.execute(child, action, opp_action)
                score = self._search_turn(child, depth - 1, alpha, beta)
                if score < worst_reply:
                    worst_reply = score
                if worst_reply <= alpha:
                    break

            if worst_reply > best_score:
                best_score = worst_reply
                best_action = action

            if best_score > alpha:
                alpha = best_score

        if best_action is None:
            best_score = self._terminal_score(state)

        self.tt.put(state, depth, best_score, best_action)
        return best_score

    def choose_action(self, state, max_depth: int = 4, time_limit_sec: float | None = None):
        if state.battle_over():
            return None, self._terminal_score(state)

        start = time.perf_counter()
        best_action = None
        best_score = -inf

        for depth in range(1, max_depth + 1):
            if time_limit_sec is not None and (time.perf_counter() - start) >= time_limit_sec:
                break

            actions = self._order_actions(state, self.generate_actions(state.player_side, state.opponent), "player")
            if not actions:
                return None, self._terminal_score(state)

            depth_best_action = None
            depth_best_score = -inf

            for action in actions:
                if time_limit_sec is not None and (time.perf_counter() - start) >= time_limit_sec:
                    break

                opp_actions = self._order_actions(state, self.generate_actions(state.opponent_side, state.player), "opponent")
                if not opp_actions:
                    opp_actions = [Action(ACTION_MOVE, move=self._first_move_name(state.opponent))]

                worst = inf
                for opp_action in opp_actions[:4]:
                    child = state.copy()
                    TurnEngine.execute(child, action, opp_action)
                    score = self._search_turn(child, depth - 1, -inf, inf)
                    if score < worst:
                        worst = score

                if worst > depth_best_score:
                    depth_best_score = worst
                    depth_best_action = action

            if depth_best_action is not None:
                best_action = depth_best_action
                best_score = depth_best_score

        return best_action, float(best_score)


SEARCHER = AlphaBetaSearchV1()

def choose_best_action(state, max_depth: int = 4, time_limit_sec: float | None = None):
    return SEARCHER.choose_action(state, max_depth=max_depth, time_limit_sec=time_limit_sec)

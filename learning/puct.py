from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
import math
import random

from battle.action import Action, ACTION_MOVE, ACTION_SWITCH
from engine.search_engine import SearchEngine
from engine.turn_engine import TurnEngine
from engine.evaluation_engine import EvaluationEngine


@dataclass
class PUCTNode:
    state: object
    parent: "PUCTNode | None" = None
    action: object | None = None
    prior: float = 1.0
    visits: int = 0
    value: float = 0.0
    children: dict[object, "PUCTNode"] = field(default_factory=dict)
    unexpanded: list[object] = field(default_factory=list)

    def q(self) -> float:
        return self.value / self.visits if self.visits else 0.0


def heuristic_prior(action) -> float:
    if action.action_type == ACTION_SWITCH:
        return 0.25
    move = str(getattr(action, "move", "")).lower()
    if move in ("protect", "recover", "tailwind"):
        return 0.9
    if move in ("swords-dance", "dragon-dance", "calm-mind"):
        return 0.85
    return 0.5


def puct_score(parent_visits: int, child: PUCTNode, c_puct: float = 1.5) -> float:
    u = c_puct * child.prior * math.sqrt(parent_visits + 1) / (1 + child.visits)
    return child.q() + u


def rollout_value(state) -> float:
    return EvaluationEngine.evaluate(state)


def simulate_once(state, depth: int = 2) -> float:
    if state.battle_over() or depth <= 0:
        return rollout_value(state)
    player_action, _ = SearchEngine.choose_best_action(state, depth=1)
    if player_action is None:
        return rollout_value(state)
    swapped = state.copy()
    opp_action, _ = SearchEngine.choose_best_action(
        type(state)(player_side=swapped.opponent_side, opponent_side=swapped.player_side),
        depth=1,
    )
    if opp_action is None:
        opp_action = Action(ACTION_MOVE, move=swapped.opponent.moves[0])
    from engine.turn_engine import TurnEngine
    TurnEngine.execute(state, player_action, opp_action)
    return simulate_once(state, depth - 1)


def puct_choose_action(state, iterations: int = 64, depth: int = 2):
    root_actions = SearchEngine.generate_actions(state.player_side, state.opponent)
    if not root_actions:
        return None

    root = PUCTNode(state=deepcopy(state), unexpanded=list(root_actions))

    for _ in range(iterations):
        node = root
        state_copy = deepcopy(root.state)

        # Selection
        while node.children and not node.unexpanded:
            node = max(node.children.values(), key=lambda ch: puct_score(node.visits, ch))

        # Expansion
        if node.unexpanded:
            action = node.unexpanded.pop(0)
            child_state = deepcopy(state_copy)
            opp_actions = SearchEngine.generate_actions(child_state.opponent_side, child_state.player)
            opp_action = opp_actions[0] if opp_actions else None
            if opp_action is None:
                from battle.action import ACTION_MOVE
                opp_action = Action(ACTION_MOVE, move=child_state.opponent.moves[0])
            TurnEngine.execute(child_state, action, opp_action)
            child = PUCTNode(
                state=child_state,
                parent=node,
                action=action,
                prior=heuristic_prior(action),
                unexpanded=list(SearchEngine.generate_actions(child_state.player_side, child_state.opponent)),
            )
            value = simulate_once(deepcopy(child_state), depth=max(1, depth - 1))
            child.visits += 1
            child.value += value
            node.children[action] = child
            node.visits += 1
            node.value += value
            continue

        # Backup
        value = rollout_value(state_copy)
        while node is not None:
            node.visits += 1
            node.value += value
            node = node.parent

    best = max(root.children.values(), key=lambda ch: ch.visits, default=None)
    return best.action if best else random.choice(root_actions)

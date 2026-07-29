from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
import math
import random


@dataclass
class Node:
    state: object
    parent: "Node | None" = None
    action: object | None = None
    children: list["Node"] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    untried_actions: list = field(default_factory=list)


def uct_score(parent_visits, child_value, child_visits, c=1.414):
    if child_visits == 0:
        return float("inf")
    return (child_value / child_visits) + c * math.sqrt(math.log(parent_visits + 1) / child_visits)


def mcts_choose_action(state, actions, rollout_fn, iterations=100):
    root = Node(state=deepcopy(state), untried_actions=list(actions))
    if not actions:
        return None

    for _ in range(iterations):
        node = root
        while node.children and not node.untried_actions:
            node = max(node.children, key=lambda ch: uct_score(node.visits, ch.value, ch.visits))

        if node.untried_actions:
            action = node.untried_actions.pop()
            child_state = deepcopy(node.state)
            reward = rollout_fn(child_state, action)
            child = Node(state=child_state, parent=node, action=action)
            child.visits += 1
            child.value += reward
            node.children.append(child)
            node.visits += 1
            node.value += reward
            continue

        reward = rollout_fn(deepcopy(node.state), None)
        while node is not None:
            node.visits += 1
            node.value += reward
            node = node.parent

    best = max(root.children, key=lambda ch: ch.visits, default=None)
    return best.action if best else random.choice(actions)

from __future__ import annotations


def format_action(action) -> str:
    if action is None:
        return "None"
    if getattr(action, "action_type", None) == "move":
        return f"move:{action.move}"
    if getattr(action, "action_type", None) == "switch":
        return f"switch:{action.switch_index}"
    return repr(action)


def format_result(result) -> str:
    return f"winner={result['winner']} turns={result['turns']} log={len(result.get('history', []))}"

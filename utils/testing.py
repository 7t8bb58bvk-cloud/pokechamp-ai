from __future__ import annotations


def assert_true(cond, msg="assertion failed"):
    if not cond:
        raise AssertionError(msg)


def assert_nonempty(obj, msg="object is empty"):
    if not obj:
        raise AssertionError(msg)


def run_minimal_suite(state, action, score):
    assert_true(state.player.current_hp > 0, "player fainted unexpectedly")
    assert_true(state.opponent.current_hp > 0, "opponent fainted unexpectedly")
    assert_nonempty(action, "no action returned")
    assert_true(isinstance(score, (int, float)), "score is not numeric")
    return True

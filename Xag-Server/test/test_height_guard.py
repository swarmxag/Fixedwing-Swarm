"""Tests for the server-side "nothing flies at a height the operator did not
give" gate, which compares against what the master itself reports."""

import re
from pathlib import Path

import pytest

from flockwave.server import height_guard

APP = Path(height_guard.__file__).with_name("app.py").read_text(encoding="utf-8")
DEFAULT_TABLE = [200, 210, 220]


def snapshot(heights=DEFAULT_TABLE, same=False, same_height=100, uavs=(1, 2, 3)):
    return {
        "uav_ids": list(uavs),
        "altitude": {
            "different_height": list(heights),
            "same_height": same_height,
            "same_alt_flag": same,
        },
    }


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(height_guard, "_expected", {})
    monkeypatch.setattr(height_guard, "_same_height", None)


def test_default_table_is_refused_until_height_is_given():
    refusal = height_guard.check(["01"], snapshot())
    assert refusal.startswith("height_not_set|")
    assert "UAV 1." in refusal

    height_guard.note_different(100, 10, [], snapshot())
    assert height_guard.check(["01"], snapshot([100, 110, 120])) is None


def test_height_uses_the_position_in_the_masters_list():
    # the swarm computes base + step * position, not position in the selection
    height_guard.note_different(100, 10, ["03"], snapshot())
    assert height_guard.check(["03"], snapshot([200, 210, 120])) is None


def test_height_for_some_uavs_does_not_cover_the_others():
    height_guard.note_different(100, 10, ["01", "02"], snapshot())
    now = snapshot([100, 110, 220])
    assert height_guard.check(["02"], now) is None
    assert "UAV 3." in height_guard.check(["03"], now)
    assert "UAV 3." in height_guard.check(["01", "03"], now)
    assert "UAV 3." in height_guard.check([], now)


def test_swarm_restart_or_new_master_back_on_defaults_is_refused():
    height_guard.note_different(100, 10, [], snapshot())
    assert height_guard.check([], snapshot([100, 110, 120])) is None
    assert "UAV 1, 2, 3." in height_guard.check([], snapshot(DEFAULT_TABLE))


def test_acknowledged_but_never_applied_is_refused():
    # e.g. a stop discarded the queued 'different'
    height_guard.note_different(100, 10, [], snapshot())
    assert height_guard.check([], snapshot(DEFAULT_TABLE)) is not None


def test_unreadable_master_is_refused():
    height_guard.note_different(100, 10, [], snapshot())
    assert height_guard.check([], None).startswith("height_not_set|")


def test_uav_joining_later_needs_its_own_height():
    height_guard.note_different(100, 10, [], snapshot())
    now = snapshot([100, 110, 120, 120], uavs=(1, 2, 3, 4))
    assert "UAV 4." in height_guard.check([], now)


def test_uav_the_master_does_not_fly_is_not_a_target():
    height_guard.note_different(100, 10, [], snapshot())
    assert height_guard.check(["01", "09"], snapshot([100, 110, 120])) is None


def test_removal_keeps_each_height_with_its_uav():
    height_guard.note_different(100, 10, [], snapshot())
    assert height_guard.check([], snapshot([100, 120], uavs=(1, 3))) is None


def test_same_height_must_match_what_the_operator_gave():
    assert height_guard.check([], snapshot(same=True)) is not None
    height_guard.note_same(150)
    assert height_guard.check([], snapshot(same=True, same_height=150)) is None
    assert height_guard.check([], snapshot(same=True, same_height=100)) is not None


def _block(msg):
    """Source of one `if msg == "..."` block of the X-UAV-socket handler."""
    found = re.findall(
        rf'^ +if msg == "{msg}":.*?(?=^ +if msg == |\Z)', APP, re.M | re.S
    )
    assert found, msg
    return re.sub(r"^\s*#.*$", "", found[-1], flags=re.M)  # code only


@pytest.mark.parametrize(
    "msg,sender",
    [
        ("goal", "goal_socket("),
        ("autogoal", "autogoal_socket("),
        ("search", "search_socket("),
        ("groupsplit", "splitmission("),
        ("spificsplit", "specificsplit("),
        ("specific_bot_goal", "specific_bot_goal_socket("),
        ("disperse", "disperse_socket("),
        ("aggregate", "aggregate_socket("),
        ("loiter", "loiter("),
        ("recover_resume", "ROUTER.resume_recovery"),
        ("home", "home_socket("),
        ("home_goto", "home_goto_socket("),
    ],
)
def test_flying_commands_check_height_before_sending_anything(msg, sender):
    block = _block(msg)
    assert "await height_refusal(" in block
    first_send = block.index(sender)
    if "stop_socket()" in block:
        first_send = min(first_send, block.index("stop_socket()"))
    assert block.index("height_refusal(") < first_send


@pytest.mark.parametrize(
    "msg", ["stop", "return", "landing", "landingmission", "fence"]
)
def test_safety_commands_are_never_refused(msg):
    assert "height_refusal(" not in _block(msg)


@pytest.mark.parametrize("msg,note", [("different", "note_different"), ("same", "note_same")])
def test_height_counts_only_once_acknowledged(msg, note):
    block = _block(msg)
    assert "if not delivery_failures:" in block
    assert block.index("_socket(") < block.index(f"height_guard.{note}(")

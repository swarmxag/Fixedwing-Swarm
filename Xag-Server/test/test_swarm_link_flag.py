"""Tests for the swarm-link ("excluded from swarm") flag of a UAV."""

from types import SimpleNamespace

import pytest

from flockwave.server.model.uav import UAVBase


class DummyDriver:
    pass


@pytest.fixture
def uav():
    return UAVBase("01", DummyDriver())  # type: ignore


def test_linked_by_default(uav):
    assert uav.status.SwarmChainLink is True


def test_set_swarm_link_reports_change(uav):
    assert uav.set_swarm_link(False) is True
    assert uav.status.SwarmChainLink is False
    # no change -> no new UAV-INF needed
    assert uav.set_swarm_link(False) is False
    assert uav.set_swarm_link(True) is True
    assert uav.status.SwarmChainLink is True


def make_server(uavs):
    """Minimal stand-in for SkybrushServer with just what the hook uses."""
    sent = []
    server = SimpleNamespace(
        object_registry=SimpleNamespace(ids_by_type=lambda cls: list(uavs)),
        find_uav_by_id=lambda uav_id: uavs.get(uav_id),
        request_to_send_UAV_INF_message_for=lambda ids: sent.append(list(ids)),
    )
    return server, sent


@pytest.fixture
def apply():
    from flockwave.server.app import SkybrushServer

    return SkybrushServer._apply_swarm_link_from_status


@pytest.mark.parametrize("status", ["completed", "running"])
def test_remove_confirmed_by_swarm_excludes_uav(apply, uav, status):
    server, sent = make_server({"01": uav})
    apply(server, {"cmd": "remove,1", "status": status})
    assert uav.status.SwarmChainLink is False
    assert sent == [["01"]]


def test_add_confirmed_by_swarm_includes_uav_again(apply, uav):
    uav.set_swarm_link(False)
    server, sent = make_server({"01": uav})
    apply(server, {"cmd": "add,1", "status": "completed"})
    assert uav.status.SwarmChainLink is True
    assert sent == [["01"]]


@pytest.mark.parametrize(
    "status", ["received", "started", "failed", "rejected", "superseded", "preempted"]
)
def test_unconfirmed_or_failed_command_changes_nothing(apply, uav, status):
    server, sent = make_server({"01": uav})
    apply(server, {"cmd": "remove,1", "status": status})
    assert uav.status.SwarmChainLink is True
    assert sent == []


def test_other_commands_and_other_uavs_are_ignored(apply, uav):
    other = UAVBase("02", DummyDriver())  # type: ignore
    server, sent = make_server({"01": uav, "02": other})
    apply(server, {"cmd": "goal_[1]", "status": "completed"})
    apply(server, {"cmd": "remove,2", "status": "completed"})
    assert uav.status.SwarmChainLink is True
    assert other.status.SwarmChainLink is False
    assert sent == [["02"]]


def test_unknown_uav_number_is_ignored(apply, uav):
    server, sent = make_server({"01": uav})
    apply(server, {"cmd": "remove,7", "status": "completed"})
    assert uav.status.SwarmChainLink is True
    assert sent == []

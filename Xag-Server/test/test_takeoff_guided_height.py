"""The first guided point after takeoff flies takeoff + slot * difference, both
entered by the operator, and never the server's altitude table."""

from types import SimpleNamespace

import pytest
import trio

from flockwave.server import app as app_module
from flockwave.server.app import SkybrushServer
from flockwave.server.socket import globalVariable

WAYPOINTS = [[float(i), float(i) + 0.5] for i in range(15)]


class FakeDriver:
    def __init__(self):
        self.sent = {}

    async def _send_fly_to_target_signal_single(self, uav, coords):
        self.sent[uav.id] = coords

    async def _send_speed_correction(self, uav, speed):
        pass


class FakeServer:
    def __init__(self, driver, ids):
        position = SimpleNamespace(ahl=100.0)
        status = SimpleNamespace(position=position)
        self.uavs = {
            id: SimpleNamespace(id=id, driver=driver, status=status) for id in ids
        }

    def find_uav_by_id(self, id):
        return self.uavs.get(id)


def fly(ids, takeoff_alt, alt_diff):
    driver = FakeDriver()

    async def run():
        await SkybrushServer.check_height(
            FakeServer(driver, ids), ids, takeoff_alt - 1, 20, WAYPOINTS, takeoff_alt, alt_diff
        )

    trio.run(run)
    return driver.sent


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    async def no_sleep(_seconds):
        await trio.lowlevel.checkpoint()

    monkeypatch.setattr(app_module, "sleep", no_sleep)


def test_height_is_takeoff_plus_slot_times_difference():
    sent = fly(["1", "2", "3"], 100, 10)
    assert [sent[id].ahl for id in ("1", "2", "3")] == [100, 110, 120]


def test_height_stays_with_the_uav_when_only_some_are_selected():
    sent = fly(["2", "5"], 100, 10)
    assert sent["2"].ahl == 110
    assert sent["5"].ahl == 140


def test_zero_difference_flies_every_uav_at_the_takeoff_height():
    sent = fly(["1", "2"], 80, 0)
    assert sent["1"].ahl == sent["2"].ahl == 80


def test_altitude_table_is_not_used(monkeypatch):
    monkeypatch.setitem(globalVariable.alts, 1, 999)
    assert fly(["1"], 100, 10)["1"].ahl == 100


def test_waypoint_is_unchanged():
    point = fly(["3"], 100, 10)["3"]
    assert (point.lat, point.lon) == (2.0, 2.5)


@pytest.mark.parametrize("alt_diff", [None, -1, "10"])
def test_takeoff_without_a_usable_difference_is_refused_before_anything_is_sent(
    monkeypatch, alt_diff
):
    updated = []
    monkeypatch.setattr(globalVariable, "update_Takeoff_Alt", updated.append)
    background = []
    server = SimpleNamespace(
        message_hub=SimpleNamespace(
            create_response_or_notification=lambda **_: SimpleNamespace()
        ),
        run_in_background=lambda *args, **kwargs: background.append(args),
    )
    body = {
        "type": "X-UAV-TAKEOFF",
        "ids": ["1"],
        "alt": 100,
        "coords": [26.0, 70.0],
        "speed": 20,
    }
    if alt_diff is not None:
        body["alt_diff"] = alt_diff

    async def run():
        await SkybrushServer.dispatch_to_uavs(
            server, SimpleNamespace(body=body), None
        )

    with pytest.raises(ValueError):
        trio.run(run)
    assert updated == []
    assert background == []

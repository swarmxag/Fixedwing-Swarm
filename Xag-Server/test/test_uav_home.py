"""Tests for the distance / bearing from the autopilot's home position."""

from types import SimpleNamespace

import pytest

from flockwave.gps.vectors import GPSCoordinate
from flockwave.server.model.uav import UAVBase


class DummyDriver:
    pass


@pytest.fixture
def uav():
    return UAVBase("01", DummyDriver())  # type: ignore


def pos(lat, lon):
    return GPSCoordinate(lat=lat, lon=lon, amsl=0, ahl=0)


def test_home_unknown_omits_fields(uav):
    uav.update_status(position=pos(13.0, 80.0))
    assert uav.home is None
    assert "homeDistance" not in uav.status
    assert "homeBearing" not in uav.status


def test_home_distance_and_bearing(uav):
    assert uav.set_home(13.0, 80.0)
    # ~111 m north of home
    uav.update_status(position=pos(13.001, 80.0))
    assert uav.status.homeDistance == pytest.approx(111.2, abs=0.5)
    assert uav.status.homeBearing == pytest.approx(0.0, abs=0.01)


def test_bearing_is_0_to_360(uav):
    uav.set_home(13.0, 80.0)
    # West of home: raw atan2 would give -90
    uav.update_status(position=pos(13.0, 79.999))
    assert uav.status.homeBearing == pytest.approx(270.0, abs=0.01)
    # South-west
    uav.update_status(position=pos(12.999, 79.999))
    assert 180 < uav.status.homeBearing < 270


def test_gcs_bearing_is_0_to_360(uav):
    uav.update_status(
        position=pos(13.0, 79.999), gcsLocation=GPSCoordinate(lat=13.0, lon=80.0)
    )
    assert uav.status.bearing == pytest.approx(270.0, abs=0.01)
    assert uav.status.distance > 0
    # GCS metrics are independent of home
    assert "homeDistance" not in uav.status


def test_set_home_after_position_is_known(uav):
    uav.update_status(position=pos(13.001, 80.0))
    uav.set_home(13.0, 80.0)
    assert uav.status.homeDistance == pytest.approx(111.2, abs=0.5)


def test_at_home_is_zero_not_missing(uav):
    uav.set_home(13.0, 80.0)
    uav.update_status(position=pos(13.0, 80.0))
    assert uav.status.homeDistance == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize(
    "lat,lon",
    [(0, 0), (91, 0), (0, 181), (float("nan"), 1), (None, None)],
)
def test_invalid_home_rejected(uav, lat, lon):
    assert not uav.set_home(lat, lon)
    assert uav.home is None


def test_invalid_position_does_not_produce_home_metrics(uav):
    uav.set_home(13.0, 80.0)
    # Drivers report 0,0 when there is no GPS fix; that must not give a
    # distance of thousands of kilometres
    uav.update_status(position=pos(0, 0))
    assert "homeDistance" not in uav.status


def test_clear_home(uav):
    uav.set_home(13.0, 80.0)
    uav.update_status(position=pos(13.001, 80.0))
    uav.clear_home()
    assert uav.home is None
    assert "homeDistance" not in uav.status
    uav.update_status(position=pos(13.002, 80.0))
    assert "homeDistance" not in uav.status


def test_home_coordinates_in_status_and_cleared(uav):
    uav.set_home(13.5, 80.25)
    assert uav.status.homeLat == 13.5
    assert uav.status.homeLon == 80.25
    uav.clear_home()
    assert "homeLat" not in uav.status
    assert "homeLon" not in uav.status


# --- Asking the autopilot for its home ----------------------------------------------


def make_requester(home=None):
    from flockwave.server.ext.mavlink.driver import MAVLinkUAV

    requests = []
    uav = SimpleNamespace(
        home=home,
        _was_armed=False,
        _home_refresh_pending=False,
        _last_home_position_requested_at=None,
        _request_home_position="request",
        driver=SimpleNamespace(run_in_background=requests.append),
    )
    heartbeat = lambda armed: MAVLinkUAV._request_home_position_if_needed(uav, armed)
    return uav, heartbeat, requests


def test_home_is_not_requested_while_disarmed():
    _, heartbeat, requests = make_requester()
    heartbeat(False)
    assert requests == []


def test_missing_home_is_requested_when_armed_and_throttled():
    _, heartbeat, requests = make_requester()
    heartbeat(True)
    heartbeat(True)
    assert len(requests) == 1


def test_known_home_is_requested_again_once_after_arming():
    uav, heartbeat, requests = make_requester(home=(47.0, 19.0))
    heartbeat(False)
    assert requests == []
    heartbeat(True)
    assert len(requests) == 1

    # the autopilot answered: no more requests while it stays armed
    uav._home_refresh_pending = False
    uav._last_home_position_requested_at = None
    heartbeat(True)
    assert len(requests) == 1


def test_request_after_arming_is_repeated_until_the_autopilot_answers():
    uav, heartbeat, requests = make_requester(home=(47.0, 19.0))
    heartbeat(True)
    uav._last_home_position_requested_at = None  # the 5 s throttle has passed
    heartbeat(True)
    assert len(requests) == 2


def test_valid_home_position_message_ends_the_refresh():
    from flockwave.server.ext.mavlink.driver import MAVLinkUAV

    def make(accepted):
        return SimpleNamespace(
            _home_refresh_pending=True,
            set_home=lambda lat, lon: accepted,
            _store_message=lambda message: None,
            notify_updated=lambda: None,
        )

    message = SimpleNamespace(latitude=470000000, longitude=190000000)
    uav = make(True)
    MAVLinkUAV.handle_message_home_position(uav, message)
    assert uav._home_refresh_pending is False

    uav = make(False)
    MAVLinkUAV.handle_message_home_position(uav, message)
    assert uav._home_refresh_pending is True

"""Geofence-related data structures and functions for the MAVLink protocol."""

from functools import partial

from flockwave.gps.vectors import GPSCoordinate
from sympy.codegen import Print
from trio import fail_after, TooSlowError
from typing import Callable, Optional, Union, List
from flockwave.logger import Logger
from .enums import MAVFrame, MAVMissionResult, MAVMissionType
from .types import (
    MAVLinkMessage,
    MAVLinkMessageSpecification,
    MAVLinkMessageMatcher,
    spec,
)
from .utils import mavlink_nav_command_to_gps_coordinate,mavlink_nav_command_to_gps_coordinate_with_frame

__all__ = ("AutoMissionManager",)


class AutoMissionManager:
    """Class responsible for retrieving and setting geofence settings on a
    MAVLink connection.
    """

    _sender: Callable
    """A function that can be called to send a MAVLink message over the
    connection associated to this MAVFTP object.

    It must be API-compatible with the `send_packet()` method of the MAVLinkUAV_
    object.
    """

    _log: Optional[Logger]
    """Logger that the manager object can use to log messages."""

    @classmethod
    def for_uav(cls, uav):
        """Constructs a MAVFTP connection object to the given UAV."""
        sender = partial(uav.driver.send_packet, target=uav)
        log = uav.driver.log
        return cls(sender, log=log)

    def __init__(
        self,
        sender: Callable,
        log: Optional[Logger] = None,
    ):
        """Constructor.

        Parameters:
            sender: a function that can be called to send a MAVLink message and
                wait for an appropriate reply
            log: optional logger to use for logging messages
        """
        self._sender = sender
        self._log = log

    async def get_automission_areas(self) -> List[List[float]]:
        """Returns the configured areas of the geofence from the MAVLink
        connection.

        Parameters:
            status: an optional input status object to update

        Returns:
            a GeofenceStatus object where the `polygons` and `circles` attributes
            will be filled appropriately with the retrieved information. All
            the other attributes will be left intact.
        """
        status = []
        # Retrieve geofence polygons and circles
        mission_type = MAVMissionType.MISSION
        reply = await self._send_and_wait(
            mission_type,
            spec.mission_request_list(mission_type=mission_type),
            spec.mission_count(mission_type=mission_type),
        )

        to_point = mavlink_nav_command_to_gps_coordinate

        # Iterate over the mission items
        for index in range(reply.count):
            reply = await self._send_and_wait(
                mission_type,
                spec.mission_request_int(seq=index, mission_type=mission_type),
                spec.mission_item_int(seq=index, mission_type=mission_type),
                timeout=0.25,
            )
            coords = to_point(reply)
            if reply.seq == 0:
                continue
            if bool(coords.lat) and bool(coords.lon):
                status.append([coords.lon, coords.lat])
        # Send final acknowledgment
        await self._send_final_ack(mission_type)

        # Return the assembled status
        return status

    async def get_AutoMisson(self) -> List[dict[str, GPSCoordinate]]:
        """Returns the configured areas of the geofence from the MAVLink
        connection.

        Parameters:
            status: an optional input status object to update

        Returns:
            a GeofenceStatus object where the `polygons` and `circles` attributes
            will be filled appropriately with the retrieved information. All
            the other attributes will be left intact.
        """
        status = []
        # Retrieve geofence polygons and circles
        mission_type = MAVMissionType.MISSION
        reply = await self._send_and_wait(
            mission_type,
            spec.mission_request_list(mission_type=mission_type),
            spec.mission_count(mission_type=mission_type),
        )

        to_point = mavlink_nav_command_to_gps_coordinate_with_frame

        # Iterate over the mission items
        for index in range(reply.count):
            reply = await self._send_and_wait(
                mission_type,
                spec.mission_request_int(seq=index, mission_type=mission_type),
                spec.mission_item_int(seq=index, mission_type=mission_type),
                timeout=0.25,
            )
            data = to_point(reply)
            if reply.seq == 0:
                continue
            status.append(data)
        # Send final acknowledgment
        await self._send_final_ack(mission_type)

        # Return the assembled status
        return status


    async def set_automission_areas(
        self,
        areas: List[float],
    ) -> None:
        """Uploads the given geofence polygons and circles to the MAVLink
        connection.

        Parameters:
            areas: the polygons and circles to upload

        Raises:
            TooSlowError: if the UAV failed to respond in time
        """
        # GPSCoordinate
        items = areas

        num_items = len(items)
        mission_type = MAVMissionType.MISSION

        index, finished = None, False
        while not finished:
            if index is None:
                # We need to let the drone know how many items there will be
                message = spec.mission_count(count=num_items, mission_type=mission_type)
                should_resend = True
            else:
                # We need to send the item with the given index to the drone
                command, kwds = items[index]
                params = {
                    "seq": index,
                    "command": command,
                    "mission_type": mission_type,
                    "param1": 0,
                    "param2": 0,
                    "param3": 0,
                    "param4": 0,
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "frame": MAVFrame.GLOBAL_RELATIVE_ALT,
                    "current": 0,
                    "autocontinue": 0,
                }
                params.update(kwds)
                message = spec.mission_item_int(**params)
                should_resend = False

            # Drone must respond with requesting the next item (or asking
            # to repeat the current one), or by sending an ACK or NAK. We should
            # _not_ attempt to re-send geofence items; it is the responsiblity
            # of the drone to request them again if they got lost.
            #
            # TODO(ntamas): we could also receive MISSION_REQUEST_INT here,
            # we need to handle both!
            expected_reply = spec.mission_request(mission_type=mission_type)
            # We have different policies for the initial message that
            # initiates the upload and the subsequent messages that are
            # responding to the requests from the drone.
            #
            # For the initial message, we attempt to re-send it in case it
            # got lost. For subsequent messages, we never re-send it (it is
            # the responsibility of the drone to request them again if our
            # reply got lost), but we assume that the upload timed out if
            # we haven't received an ACK or the next request from the drone
            # in five seconds.
            reply = await self._send_and_wait(
                mission_type,
                message,
                expected_reply,
                timeout=1.5 if should_resend else 5,
                retries=5 if should_resend else 0,
            )
            if reply is None:
                # Final ACK received
                finished = True
            else:
                # Drone requested another item
                index = reply.seq
                # if index is None:
                #     index = 0
                # else:
                #     index = index + 1
                #     if num_items == index:
                #         finished = True

    async def upload_AutoMission(
        self,
        areas: List[float],
    ) -> None:
        """Uploads the given geofence polygons and circles to the MAVLink
        connection.

        Parameters:
            areas: the polygons and circles to upload

        Raises:
            TooSlowError: if the UAV failed to respond in time
        """
        # GPSCoordinate
        items = areas

        num_items = len(items)
        mission_type = MAVMissionType.MISSION

        index, finished = None, False
        while not finished:
            print(index,finished)
            if index is None:
                # We need to let the drone know how many items there will be
                message = spec.mission_count(count=num_items, mission_type=mission_type)
                should_resend = True
            else:
                # We need to send the item with the given index to the drone
                command, kwds = items[index]
                params = {
                    "seq": index,
                    "command": command,
                    "mission_type": mission_type,
                    "param1": 0,
                    "param2": 0,
                    "param3": 0,
                    "param4": 0,
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "frame": MAVFrame.GLOBAL_RELATIVE_ALT,
                    "current": 0,
                    "autocontinue": 0,
                }
                params.update(kwds)
                message = spec.mission_item_int(**params)
                should_resend = False

            # Drone must respond with requesting the next item (or asking
            # to repeat the current one), or by sending an ACK or NAK. We should
            # _not_ attempt to re-send geofence items; it is the responsiblity
            # of the drone to request them again if they got lost.
            #
            # TODO(ntamas): we could also receive MISSION_REQUEST_INT here,
            # we need to handle both!
            expected_reply = spec.mission_request(mission_type=mission_type)
            # We have different policies for the initial message that
            # initiates the upload and the subsequent messages that are
            # responding to the requests from the drone.
            #
            # For the initial message, we attempt to re-send it in case it
            # got lost. For subsequent messages, we never re-send it (it is
            # the responsibility of the drone to request them again if our
            # reply got lost), but we assume that the upload timed out if
            # we haven't received an ACK or the next request from the drone
            # in five seconds.
            reply = await self._send_and_wait(
                mission_type,
                message,
                expected_reply,
                timeout=1.5 if should_resend else 5,
                retries=5 if should_resend else 0,
            )
            if reply is None:
                # Final ACK received
                finished = True
            else:
                # Drone requested another item
                index = reply.seq
                # if index is None:
                #     index = 0
                # else:
                #     index = index + 1
                #     if num_items == index:
                #         finished = True


    async def clear_mission(self):
        mission_type = MAVMissionType.MISSION
        reply = await self._send_and_wait(
            mission_type,
            spec.mission_clear_all(mission_type=mission_type),
            spec.mission_ack(mission_type=mission_type),
        )
        return reply

    async def _send_and_wait(
        self,
        mission_type: MAVMissionType,
        message: MAVLinkMessageSpecification,
        expected_reply: MAVLinkMessageMatcher,
        *,
        timeout: float = 1.5,
        retries: int = 5,
    ) -> MAVLinkMessage:
        """Sends a message according to the given MAVLink message specification
        to the drone and waits for an expected reply, re-sending the message
        as needed a given number of times before timing out.

        Parameters:
            mission_type: type of the mission we are dealing with
            message: specification of the message to send
            expected_reply: message matcher that matches messages that we expect
                from the connection as a reply to the original message
            timeout: maximum number of seconds to wait before attempting to
                re-send the message
            retries: maximum number of retries before giving up

        Returns:
            the MAVLink message sent by the UAV in response

        Raises:
            TooSlowError: if the UAV failed to respond in time
        """
        # For each mission-related message that we send, we could receive either
        # the expected response or a MISSION_ACK with an error code.
        if expected_reply[0] == "MISSION_ACK":
            replies = {"ack": expected_reply}
        else:
            replies = {
                "response": expected_reply,
                "ack": spec.mission_ack(mission_type=mission_type),
            }

        while True:
            try:
                with fail_after(timeout):
                    key, response = await self._sender(message, wait_for_one_of=replies)
                    if key == "response":
                        # Got the response that we expected
                        return response
                    else:
                        # Got an ACK. Check whether it has an error code.
                        if response.type == MAVMissionResult.ACCEPTED:
                            return None
                        else:
                            raise RuntimeError(
                                f"MAVLink mission operation returned code {response.type}"
                            )

            except TooSlowError:
                if retries > 0:
                    retries -= 1
                    continue
                else:
                    raise TooSlowError("MAVLink mission operation timed out") from None

    async def _send_final_ack(self, mission_type: int) -> None:
        """Sends the final acknowledgment at the end of a mission download
        transaction.
        """
        try:
            await self._sender(spec.mission_ack(type=mission_type))
        except Exception as ex:
            # doesn't matter, we got what we needed
            print(repr(ex))

// coverage: 500,
//   gridSpacing: 50,
//   Direction: 'Anti ClockWise Direction', ..
//   groups: [],
//   addedUavs_ids: [],
//   skip_waypoint: 0, ..
//   radius:0, ..
//   speed:18, ..

import { getFeaturesInOrder } from '../map-features/selectors';

/**
 * Returns the current value of skip_waypoint.
 *
 * @param  {Object}  state  the state of the application
 */
export const getSkipWaypoint = (state) => state.socket.skip_waypoint;

export const getDirection = (state) => state.socket.Direction;

export const getRadius = (state) => state.socket.radius;

export const getSpeed = (state) => state.socket.speed;

export const getBaseAltitude = (state) => state.socket.baseAltitude;

export const getAltitudeStep = (state) => state.socket.altitudeStep;

export const getGrisSpacing = (state) => state.socket.gridSpacing;

export const getCoverage = (state) => state.socket.coverage;

export const getFeatureByPoints = (state) => {
  const feature = getFeaturesInOrder(state);
  const points = feature.filter((item) => item.type === 'points');
  return points;
};

export const getGroup = (state) =>
  Object.entries(state.socket.group).map(([key, values]) => ({
    marker: key,
    values: values,
  }));

export const getGroupByObject = (state) => state.socket.group;

export const valueExists = (state, listTocheck) =>
  listTocheck.some((value) =>
    Object.values(state.socket.group).some((arr) => arr.includes(value))
  );

export const getMissionByUav = (state) => state.socket.missionByUav;

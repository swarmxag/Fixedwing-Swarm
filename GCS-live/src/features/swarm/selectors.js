// coverage: 500,
//   gridSpacing: 50,
//   Direction: 'Anti ClockWise Direction', ..
//   groups: [],
//   addedUavs_ids: [],
//   skip_waypoint: 0, ..
//   radius:0, ..
//   speed:18, ..

import { createSelector } from '@reduxjs/toolkit';

import { FeatureType } from '~/model/features';
import { getSelectedFeatureIds } from '~/features/map-features/selectors';
import { getSelectedUAVIds, getUAVIdList } from '~/features/uavs/selectors';

import {
  DEFAULT_BEARING_DEG,
  DEFAULT_SAFETY_MARGIN_M,
  generateLoiterGoalPoints,
  loiterCenterSpacing,
} from './loiter-preview';

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

/**
 * The "Automate Goals" layout the CURRENT panel inputs would produce, for
 * the map to draw as a live preview -- one loiter centre and one circle per
 * UAV, laid out exactly the way the swarm computer will lay them out when
 * the button is pressed.
 *
 * Recomputed by the store on every keystroke in the bearing / safety margin
 * boxes (and on a loiter-radius or selection change), which is what makes
 * the preview move "on spot while changing" without anything being sent.
 *
 * Returns undefined -- i.e. draw nothing -- unless the command would
 * actually be accepted: a drawn point selected to anchor it (handlePoint
 * uses selectedFeatureIds[0] and the swarm computer takes coords[0]), and a
 * positive loiter radius (_apply_autogoal bails on radius <= 0).
 */
export const getAutoGoalPreview = createSelector(
  getSelectedFeatureIds,
  (state) => state.features.byId,
  getSelectedUAVIds,
  getUAVIdList,
  (state) => state.socket,
  (selectedFeatureIds, featuresById, selectedUAVIds, allUAVIds, socket) => {
    const anchorFeature = featuresById[selectedFeatureIds[0]];
    if (anchorFeature?.type !== FeatureType.POINTS) {
      return undefined;
    }

    // Feature points are [lon, lat]; swarm.py's autogoal_socket reverses
    // them to [lat, lon] on the wire, and only coords[0] is ever used.
    const anchor = anchorFeature.points?.[0];
    if (!anchor) {
      return undefined;
    }

    const loiterRadiusM = Number(socket.radius);
    if (!(loiterRadiusM > 0)) {
      return undefined;
    }

    // An empty id list means "the whole swarm" on the swarm computer
    // (utils.selected_swarm_indexes returns every index for []), so the
    // preview has to fan out over every connected UAV in that case.
    const numUavs =
      selectedUAVIds.length > 0 ? selectedUAVIds.length : allUAVIds.length;
    if (numUavs < 1) {
      return undefined;
    }

    const bearingDeg = Number.isFinite(socket.automateBearing)
      ? socket.automateBearing
      : DEFAULT_BEARING_DEG;
    const safetyMarginM = Number.isFinite(socket.automateSafetyMargin)
      ? socket.automateSafetyMargin
      : DEFAULT_SAFETY_MARGIN_M;

    const [lon, lat] = anchor;

    return {
      centers: generateLoiterGoalPoints({
        lat,
        lon,
        numUavs,
        loiterRadiusM,
        bearingDeg,
        safetyMarginM,
      }),
      loiterRadiusM,
      bearingDeg,
      safetyMarginM,
      spacingM: loiterCenterSpacing(loiterRadiusM, safetyMarginM),
    };
  }
);

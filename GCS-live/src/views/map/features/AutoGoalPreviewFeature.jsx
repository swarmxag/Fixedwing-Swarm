/**
 * @file Map preview of the "Automate Goals" layout: one loiter circle per
 * UAV, the spine they march along, and the safety-margin gap between
 * consecutive circles.
 *
 * Nothing here talks to the server. The geometry comes from
 * features/swarm/loiter-preview.js, a port of the swarm computer's
 * goal_point_generator.py, so what is drawn is what the swarm computer
 * would compute for the inputs currently in the panel -- redrawn on every
 * keystroke, before anything is sent.
 *
 * The gap segment is the point of the overlay: the safety margin is the
 * clearance between two circle EDGES, not something added to the radius,
 * and that is very hard to judge from the circles alone once the radius is
 * large (2000 m circles with a 100 m margin look like they are touching --
 * because they nearly are).
 */

import PropTypes from 'prop-types';
import React from 'react';

import { Feature, geom } from '@collmot/ol-react';
import { Circle, Style, Text } from 'ol/style';

import {
  destinationPoint,
  loiterCircleRing,
} from '~/features/swarm/loiter-preview';
import { mapViewCoordinateFromLonLat } from '~/utils/geography';
import { fill, stroke } from '~/utils/styles';

// Same palette (and order) as the per-UAV mission overlay in
// layers/mission-info.jsx, so a UAV's preview circle and its downloaded
// path read as the same colour.
const uavColors = [
  '#cd5c5c',
  '#ffa500',
  '#40e0d0',
  '#ff7f50',
  '#87cefa',
  '#da70d6',
  '#32cd32',
  '#6495ed',
  '#ff69b4',
  '#ba55d3',
];

const GAP_COLOR = '#ff1744';

const formatMetres = (value) =>
  `${Number.isInteger(value) ? value : value.toFixed(1)} m`;

const labelText = (text, color, offsetY = 0) =>
  new Text({
    text,
    font: '600 11px sans-serif',
    fill: fill(color),
    stroke: stroke('rgba(0, 0, 0, 0.85)', 3),
    offsetY,
    overflow: true,
  });

// Styles are keyed by colour and built once: OpenLayers re-renders the
// whole vector source on every pan/zoom, and this overlay re-renders on
// every keystroke in the panel, so allocating fresh Style objects per
// render would churn hard for no benefit.
const circleStyleCache = new Map();
const circleStyle = (color) => {
  if (!circleStyleCache.has(color)) {
    circleStyleCache.set(
      color,
      new Style({ stroke: stroke(color, 2, [6, 6]) })
    );
  }

  return circleStyleCache.get(color);
};

const centerStyleCache = new Map();
const centerStyle = (color, label) => {
  const key = `${color}|${label}`;
  if (!centerStyleCache.has(key)) {
    centerStyleCache.set(
      key,
      new Style({
        image: new Circle({
          radius: 4,
          fill: fill(color),
          stroke: stroke('white', 1.5),
        }),
        text: labelText(label, color, -14),
      })
    );
  }

  return centerStyleCache.get(key);
};

const spineStyle = new Style({
  stroke: stroke('rgba(255, 255, 255, 0.85)', 1, [2, 6]),
});

const gapStyleCache = new Map();
const gapStyle = (label) => {
  if (!gapStyleCache.has(label)) {
    gapStyleCache.set(
      label,
      new Style({
        stroke: stroke(GAP_COLOR, 3),
        text: labelText(label, GAP_COLOR, -10),
      })
    );
  }

  return gapStyleCache.get(label);
};

/**
 * Builds the preview's OpenLayers features for a vector source.
 *
 * Returns a plain array of <Feature> elements rather than a component so it
 * can be spread into the mission-info layer's own feature list, the way
 * that layer already assembles home/landing/trajectory features.
 */
export function createAutoGoalPreviewFeatures(preview) {
  const { centers, loiterRadiusM, bearingDeg, safetyMarginM, spacingM } =
    preview ?? {};

  if (!Array.isArray(centers) || centers.length === 0) {
    return [];
  }

  const features = [];

  for (const [index, center] of centers.entries()) {
    const color = uavColors[index % uavColors.length];

    features.push(
      // The loiter circle itself, at the radius the layout was spaced for.
      <Feature
        key={`autogoal.preview.circle.${index}`}
        style={circleStyle(color)}
      >
        <geom.LineString
          coordinates={loiterCircleRing(
            center.lat,
            center.lon,
            loiterRadiusM
          ).map((point) => mapViewCoordinateFromLonLat(point))}
        />
      </Feature>,

      // The centre, labelled with the UAV's slot in the layout and how far
      // along the bearing it sits. Slot 1 is the drawn point itself, which
      // is why it never moves when the margin changes.
      <Feature
        key={`autogoal.preview.center.${index}`}
        style={centerStyle(
          color,
          index === 0
            ? `1 · r ${formatMetres(loiterRadiusM)} · brg ${bearingDeg}°`
            : `${center.index} · ${formatMetres(center.distanceM)}`
        )}
      >
        <geom.Point
          coordinates={mapViewCoordinateFromLonLat([center.lon, center.lat])}
        />
      </Feature>
    );
  }

  // Spine through every centre: the line the layout marches along, i.e. the
  // bearing made visible.
  if (centers.length > 1) {
    features.push(
      <Feature key='autogoal.preview.spine' style={spineStyle}>
        <geom.LineString
          coordinates={centers.map((center) =>
            mapViewCoordinateFromLonLat([center.lon, center.lat])
          )}
        />
      </Feature>
    );
  }

  // One gap segment per neighbouring pair, spanning the open air between
  // the two facing edges. Its length IS the safety margin: it runs from
  // radius-along-bearing off the near centre to radius-against-bearing off
  // the far one, and centre spacing is 2r + margin.
  for (let index = 0; index < centers.length - 1; index++) {
    const near = centers[index];
    const far = centers[index + 1];
    const [nearEdgeLat, nearEdgeLon] = destinationPoint(
      near.lat,
      near.lon,
      bearingDeg,
      loiterRadiusM
    );
    const [farEdgeLat, farEdgeLon] = destinationPoint(
      far.lat,
      far.lon,
      bearingDeg + 180,
      loiterRadiusM
    );

    features.push(
      <Feature
        key={`autogoal.preview.gap.${index}`}
        style={gapStyle(
          index === 0
            ? `gap ${formatMetres(safetyMarginM)} (spacing ${formatMetres(
                spacingM
              )})`
            : `gap ${formatMetres(safetyMarginM)}`
        )}
      >
        <geom.LineString
          coordinates={[
            mapViewCoordinateFromLonLat([nearEdgeLon, nearEdgeLat]),
            mapViewCoordinateFromLonLat([farEdgeLon, farEdgeLat]),
          ]}
        />
      </Feature>
    );
  }

  return features;
}

export const AutoGoalPreviewPropType = PropTypes.shape({
  centers: PropTypes.arrayOf(
    PropTypes.shape({
      index: PropTypes.number,
      lat: PropTypes.number,
      lon: PropTypes.number,
      distanceM: PropTypes.number,
    })
  ),
  loiterRadiusM: PropTypes.number,
  bearingDeg: PropTypes.number,
  safetyMarginM: PropTypes.number,
  spacingM: PropTypes.number,
});

/**
 * @file Shows the terrain that is above the current safety threshold as red
 * areas on the map (Step 4B of the terrain safety system).
 *
 * Xag-Server sends the areas as polygons (with holes) in
 * `X-TERRAIN-UNSAFE-AREA-RESP` messages; this file draws them, shows a small
 * legend with a show/hide switch, and asks the server for the current state
 * whenever the GCS connects (it may have missed the last broadcast).
 */

import { Fill, Stroke, Style } from 'ol/style';
import PropTypes from 'prop-types';
import React, { useEffect, useMemo } from 'react';
import { connect } from 'react-redux';

import Typography from '@material-ui/core/Typography';

import { Feature, geom, layer, source } from '@collmot/ol-react';

import Widget from '~/components/Widget';
import { getCurrentServerState } from '~/features/servers/selectors';
import {
  areaToRings,
  describeThresholdBreakdown,
  describeUnsafeTerrain,
} from '~/features/terrain-safety/areas';
import { requestUnsafeTerrain } from '~/features/terrain-safety/request';
import {
  getUnsafeTerrain,
  isUnsafeTerrainVisible,
} from '~/features/terrain-safety/selectors';
import { clearUnsafeTerrain } from '~/features/terrain-safety/slice';
import { ConnectionState } from '~/model/enums';
import { mapViewCoordinateFromLonLat } from '~/utils/geography';

const FILL_COLOR = 'rgba(255, 0, 0, 0.35)';
const STROKE_COLOR = 'rgba(200, 0, 0, 0.9)';

// area.severity === 'yellow': the live UAV has reached/passed this area's
// terrain but not yet cleared the safety margin (computed server-side by
// Xag-Server's terrain_areas.attach_area_severity; never recomputed here).
const YELLOW_FILL_COLOR = 'rgba(255, 200, 0, 0.35)';
const YELLOW_STROKE_COLOR = 'rgba(200, 150, 0, 0.9)';

const unsafeAreaStyle = new Style({
  fill: new Fill({ color: FILL_COLOR }),
  stroke: new Stroke({ color: STROKE_COLOR, width: 1.5 }),
});

const unsafeAreaYellowStyle = new Style({
  fill: new Fill({ color: YELLOW_FILL_COLOR }),
  stroke: new Stroke({ color: YELLOW_STROKE_COLOR, width: 1.5 }),
});

// Above the base map, below everything else (graticule, features, UAVs, ...).
const Z_INDEX = 0.5;

// === The red areas ===

const TerrainUnsafeAreasLayerPresentation = ({ unsafeTerrain, visible }) => {
  // Nothing is drawn unless both hold, so nothing needs projecting either.
  const shouldRender = visible && unsafeTerrain?.status === 'unsafe';

  // Projecting thousands of vertices is worth doing only when the areas change
  // -- and only when they are actually on screen. The threshold is recalculated
  // on every ~5 m of altitude, so without the `shouldRender` guard, turning the
  // layer off would still re-project every vertex on each of those updates.
  const areas = useMemo(
    () =>
      shouldRender
        ? (unsafeTerrain?.areas ?? []).map((area) => ({
            id: area.id,
            rings: areaToRings(area, mapViewCoordinateFromLonLat),
            // The SERVER already decided this (Xag-Server's
            // terrain_areas.attach_area_severity, from the live UAV altitude);
            // the frontend only ever reads it back. `undefined` (an older
            // server) keeps the plain red, same as before this field existed.
            severity: area.severity,
          }))
        : [],
    [unsafeTerrain, shouldRender]
  );

  if (!shouldRender || areas.length === 0) {
    return null;
  }

  return (
    <layer.Vector zIndex={Z_INDEX}>
      <source.Vector>
        {areas.map(({ id, rings: [exterior, ...holes], severity }) => (
          <Feature
            key={`unsafeTerrain.${id}`}
            style={
              severity === 'yellow' ? unsafeAreaYellowStyle : unsafeAreaStyle
            }
          >
            <geom.Polygon coordinates={exterior} holes={holes} />
          </Feature>
        ))}
      </source.Vector>
    </layer.Vector>
  );
};

TerrainUnsafeAreasLayerPresentation.propTypes = {
  unsafeTerrain: PropTypes.object,
  visible: PropTypes.bool,
};

export const TerrainUnsafeAreasLayer = connect((state) => ({
  unsafeTerrain: getUnsafeTerrain(state),
  visible: isUnsafeTerrainVisible(state),
}))(TerrainUnsafeAreasLayerPresentation);

// === Legend with a show/hide switch ===

const thresholdSourceHint = ({ thresholdUavId, altitudeSource }) => {
  const who = thresholdUavId ? `UAV ${thresholdUavId}` : 'the Origin default';
  return `Safety threshold of ${who}${altitudeSource ? ` (${altitudeSource})` : ''}`;
};

const BreakdownRow = ({ label, value, bold }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
    <Typography variant='caption' color='textSecondary'>
      {label}
    </Typography>
    <Typography
      variant='caption'
      style={{ marginLeft: 16, fontWeight: bold ? 'bold' : 'normal' }}
    >
      {value}
    </Typography>
  </div>
);

BreakdownRow.propTypes = {
  label: PropTypes.string,
  value: PropTypes.string,
  bold: PropTypes.bool,
};

const TerrainSafetyWidgetPresentation = ({ unsafeTerrain, visible }) => {
  // The on/off switch lives in the Swarm panel; this only reports.
  if (!visible || !unsafeTerrain) {
    return null;
  }

  // The numbers the SERVER calculated the threshold from; only shown, never recomputed
  const breakdown = describeThresholdBreakdown(unsafeTerrain);

  return (
    <Widget
      showControls={false}
      // Right of the map's toolbars (they occupy the left edge, ~68 px, and used to
      // cover the start of every line here) and above the scale line
      style={{ bottom: 48, left: 80, minWidth: 260 }}
    >
      <div
        title={thresholdSourceHint(unsafeTerrain)}
        style={{ padding: '4px 8px' }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div
            style={{
              width: 14,
              height: 14,
              marginRight: 8,
              background: FILL_COLOR,
              border: `1.5px solid ${STROKE_COLOR}`,
            }}
          />
          <Typography variant='body2' style={{ flexGrow: 1 }}>
            {describeUnsafeTerrain(unsafeTerrain)}
          </Typography>
        </div>
        {breakdown && (
          <div style={{ paddingBottom: 4 }}>
            <BreakdownRow label='Home terrain' value={breakdown.homeTerrain} />
            {breakdown.homeSource && (
              <Typography
                variant='caption'
                color='textSecondary'
                component='div'
                style={{ marginBottom: 2, fontStyle: 'italic' }}
              >
                {breakdown.homeSource}
              </Typography>
            )}
            <BreakdownRow label='Drone height' value={breakdown.droneHeight} />
            <BreakdownRow
              label='Safety margin'
              value={breakdown.safetyMargin}
            />
            {/* <BreakdownRow
              label='Highest terrain peak'
              value={breakdown.highestPeak}
            /> */}
            <BreakdownRow
              bold
              label='Drone safe altitude'
              value={breakdown.droneSafeAltitude}
            />
            {/* {breakdown.safeAltitudeFormula && (
              <Typography
                variant='caption'
                color='textSecondary'
                component='div'
                // "safe altitude" is a height above home (AGL-style), unlike
                // the AMSL elevations above it -- spelled out here since the
                // row above only shows a bare "m", the same as drone height
                title='Height above home needed to clear the highest peak by the safety margin (not an AMSL elevation)'
              >
                {breakdown.safeAltitudeFormula}
              </Typography>
            )} */}
            <BreakdownRow
              bold
              label='Safety threshold'
              value={breakdown.threshold}
            />
            {/* <Typography variant='caption' color='textSecondary' component='div'>
              {breakdown.formula}
            </Typography> */}
          </div>
        )}
      </div>
    </Widget>
  );
};

TerrainSafetyWidgetPresentation.propTypes = {
  unsafeTerrain: PropTypes.object,
  visible: PropTypes.bool,
};

export const TerrainSafetyWidget = connect((state) => ({
  unsafeTerrain: getUnsafeTerrain(state),
  visible: isUnsafeTerrainVisible(state),
}))(TerrainSafetyWidgetPresentation);

// === Keeps the state in step with the server connection ===

const TerrainSafetySyncPresentation = ({ connection, dispatch }) => {
  useEffect(() => {
    if (connection === ConnectionState.CONNECTED) {
      // We may have missed the broadcast that was sent before we connected.
      requestUnsafeTerrain(dispatch);
    } else {
      // Never keep showing red areas that came from a server we left.
      dispatch(clearUnsafeTerrain());
    }
  }, [connection, dispatch]);

  return null;
};

TerrainSafetySyncPresentation.propTypes = {
  connection: PropTypes.string,
  dispatch: PropTypes.func,
};

export const TerrainSafetySync = connect((state) => ({
  connection: getCurrentServerState(state).state,
}))(TerrainSafetySyncPresentation);

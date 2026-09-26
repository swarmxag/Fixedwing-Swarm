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
import { getUid } from 'ol/util';  // TEMP-TERRAIN-MAP
import React, { useEffect, useMemo, useRef } from 'react';
import { connect } from 'react-redux';

import Switch from '@material-ui/core/Switch';
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
import {
  clearUnsafeTerrain,
  setUnsafeTerrainVisible,
} from '~/features/terrain-safety/slice';
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

// ===== TEMP-TERRAIN-MAP (temporary diagnostics; delete this block, the `ref`/`useRef`/`useEffect` marked
// TEMP-TERRAIN-MAP below and the `getUid` import) =====
// Logs what the OpenLayers VectorSource REALLY holds: CREATE / UPDATE / REMOVE events of its features and,
// after every render, one line per area plus a check that the map holds exactly the areas of the message.
// Everything is also kept in window.__terrainMapTrace (last 400 lines):
//   copy(window.__terrainMapTrace.join(String.fromCharCode(10)))
const flatHash = (flat) => {
  let h = 0;
  for (const v of flat) h = (Math.imul(h, 31) + Math.round(v * 100)) | 0;
  return (h >>> 0).toString(16);
};
const ringsFlat = (rings) => rings.flat(2);
const geomLabel = (flat) => `${flat.length / 2}v#${flatHash(flat)}`;
const colorName = (style) => {
  const c = style?.getFill?.()?.getColor?.();
  return c === FILL_COLOR ? 'red' : c === YELLOW_FILL_COLOR ? 'yellow' : String(c);
};
const featureLabel = (f) => {
  const g = f.getGeometry();
  return `feature=${getUid(f)} color=${colorName(f.getStyle())} geom=${g ? geomLabel(g.getFlatCoordinates()) : 'none'}`;
};
const traceLog = (line) => {
  const w = window;
  w.__terrainMapTrace = [...(w.__terrainMapTrace ?? []).slice(-399), line];
  console.log(line);
};
function attachSourceTrace(source) {
  if (!source || source.__terrainTraced) {
    return;
  }

  source.__terrainTraced = true;
  source.on('addfeature', (e) => traceLog(`[TERRAIN-MAP] action=CREATE ${featureLabel(e.feature)}`));
  source.on('removefeature', (e) => traceLog(`[TERRAIN-MAP] action=REMOVE ${featureLabel(e.feature)}`));
  source.on('changefeature', (e) => traceLog(`[TERRAIN-MAP] action=UPDATE ${featureLabel(e.feature)}`));
}

function traceRender(unsafeTerrain, areas, source) {
  const features = source ? source.getFeatures() : [];
  const held = features.map((f) => ({
    f,
    color: colorName(f.getStyle()),
    geom: geomLabel(f.getGeometry().getFlatCoordinates()),
  }));
  const problems = [];
  const wanted = (unsafeTerrain?.areas ?? []).map((area, i) => ({
    id: area.id,
    severity: area.severity ?? 'red(undefined)',
    color: area.severity === 'yellow' ? 'yellow' : 'red',
    maxElevation: area.maxElevation,
    geom: geomLabel(ringsFlat(areas[i].rings)),
  }));
  const pool = [...held];
  for (const a of wanted) {
    const at = pool.findIndex((h) => h.geom === a.geom && h.color === a.color);
    const anyGeom = held.find((h) => h.geom === a.geom);
    traceLog(
      `[TERRAIN-MAP] id=${a.id} severity=${a.severity} maxElevation=${a.maxElevation} geom=${a.geom} -> ` +
        (anyGeom ? `map has ${anyGeom.color} ${featureLabel(anyGeom.f)}` : 'NO map feature with this geometry')
    );
    if (at >= 0) {
      pool.splice(at, 1);
    } else {
      problems.push(`area id=${a.id} (${a.color}) not shown as such`);
    }
  }

  for (const h of pool) {
    problems.push(`EXTRA feature on map: ${featureLabel(h.f)}`);
  }

  traceLog(
    `[TERRAIN-MAP] SNAPSHOT areas=${wanted.length} mapFeatures=${held.length} ` +
      `red=${held.filter((h) => h.color === 'red').length} yellow=${held.filter((h) => h.color === 'yellow').length} ` +
      (problems.length === 0 ? 'OK' : `PROBLEM: ${problems.join('; ')}`)
  );
}
// ===== end TEMP-TERRAIN-MAP =====

// === The red areas ===

const TerrainUnsafeAreasLayerPresentation = ({ unsafeTerrain, visible }) => {
  // Projecting thousands of vertices is worth doing only when the areas change
  const areas = useMemo(
    () =>
      (unsafeTerrain?.areas ?? []).map((area) => ({
        id: area.id,
        rings: areaToRings(area, mapViewCoordinateFromLonLat),
        // The SERVER already decided this (Xag-Server's
        // terrain_areas.attach_area_severity, from the live UAV altitude);
        // the frontend only ever reads it back. `undefined` (an older
        // server) keeps the plain red, same as before this field existed.
        severity: area.severity,
      })),
    [unsafeTerrain]
  );

  const traceSourceRef = useRef(null); // TEMP-TERRAIN-MAP
  useEffect(() => {
    // TEMP-TERRAIN-MAP: runs after every render, when the OpenLayers features are up to date
    const source = traceSourceRef.current?.source;
    attachSourceTrace(source);
    traceRender(unsafeTerrain, areas, source);
  });

  if (!visible || unsafeTerrain?.status !== 'unsafe' || areas.length === 0) {
    return null;
  }

  return (
    <layer.Vector zIndex={Z_INDEX}>
      <source.Vector ref={traceSourceRef}>{/* TEMP-TERRAIN-MAP */}
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

const TerrainSafetyWidgetPresentation = ({
  unsafeTerrain,
  visible,
  onToggle,
}) => {
  if (!unsafeTerrain) {
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
              opacity: visible ? 1 : 0.4,
            }}
          />
          <Typography variant='body2' style={{ flexGrow: 1 }}>
            {describeUnsafeTerrain(unsafeTerrain)}
          </Typography>
          <Switch
            size='small'
            checked={visible}
            inputProps={{ 'aria-label': 'Show unsafe terrain on the map' }}
            onChange={(event) => onToggle(event.target.checked)}
          />
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
  onToggle: PropTypes.func,
};

export const TerrainSafetyWidget = connect(
  (state) => ({
    unsafeTerrain: getUnsafeTerrain(state),
    visible: isUnsafeTerrainVisible(state),
  }),
  { onToggle: setUnsafeTerrainVisible }
)(TerrainSafetyWidgetPresentation);

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

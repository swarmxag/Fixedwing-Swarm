/**
 * @file Client-side mirror of the swarm computer's "Automate Goals" layout
 * math, so the map can draw the loiter circles the command WOULD produce
 * before it is sent -- and redraw them live while the operator types a new
 * bearing, safety margin or loiter radius.
 *
 * This is a deliberate duplication of
 * medur_swarm/goal_point_generator.py. The preview is only worth anything
 * if it agrees with the swarm computer to the metre, so the constant and
 * the two formulae below are kept equivalent to that file line for line:
 *
 *   EARTH_RADIUS_M      -> goal_point_generator.EARTH_RADIUS_M
 *   destinationPoint    -> goal_point_generator.destination_point
 *   loiterCenterSpacing -> goal_point_generator.loiter_center_spacing
 *
 * If the Python changes, change this too.
 */

export const EARTH_RADIUS_M = 6371000;

/**
 * Fallbacks mirroring goal_point_generator.py's module-level defaults.
 *
 * These only cover a genuinely missing value (an older store shape). A box
 * the operator blanked out sends 0, not undefined -- `Number.parseFloat('')
 * || 0` in SwarmPanel.jsx -- and 0 is a valid margin that the swarm
 * computer honours, so the preview must show touching circles for it
 * rather than quietly substituting 50.
 */
export const DEFAULT_BEARING_DEG = 90;
export const DEFAULT_SAFETY_MARGIN_M = 50;

const toRadians = (degrees) => (degrees * Math.PI) / 180;
const toDegrees = (radians) => (radians * 180) / Math.PI;

/**
 * Lat/lon reached by travelling `distanceM` from (lat, lon) along the great
 * circle at compass bearing `bearingDeg`. Returns [lat, lon] in degrees --
 * lat first, matching the Python it mirrors, NOT the [lon, lat] order the
 * map layer wants.
 */
export function destinationPoint(lat, lon, bearingDeg, distanceM) {
  const lat1 = toRadians(lat);
  const lon1 = toRadians(lon);
  const bearing = toRadians(bearingDeg);
  const angularDistance = distanceM / EARTH_RADIUS_M;

  const lat2 = Math.asin(
    Math.sin(lat1) * Math.cos(angularDistance) +
      Math.cos(lat1) * Math.sin(angularDistance) * Math.cos(bearing)
  );

  const lon2 =
    lon1 +
    Math.atan2(
      Math.sin(bearing) * Math.sin(angularDistance) * Math.cos(lat1),
      Math.cos(angularDistance) - Math.sin(lat1) * Math.sin(lat2)
    );

  return [toDegrees(lat2), toDegrees(lon2)];
}

/**
 * Centre-to-centre distance between two consecutive loiter circles.
 *
 * Decomposes as `r + margin + r`: the safety margin is the open gap left
 * between the two circle EDGES, it is not added to either radius.
 */
export const loiterCenterSpacing = (loiterRadiusM, safetyMarginM) =>
  2 * loiterRadiusM + safetyMarginM;

/**
 * One loiter centre per UAV, marching along `bearingDeg` from the operator's
 * single drawn point.
 *
 * UAV 1 sits exactly on that point (distance 0) and never moves when the
 * margin changes; UAV 2..N step out by one `loiterCenterSpacing` each, so a
 * margin change displaces the last UAV the most.
 *
 * Returns [{ index, lat, lon, distanceM }], index 1-based to match the
 * swarm computer's uav_id.
 */
export function generateLoiterGoalPoints({
  lat,
  lon,
  numUavs,
  loiterRadiusM,
  bearingDeg = DEFAULT_BEARING_DEG,
  safetyMarginM = DEFAULT_SAFETY_MARGIN_M,
}) {
  if (!(numUavs >= 1) || !(loiterRadiusM > 0)) {
    return [];
  }

  const spacing = loiterCenterSpacing(loiterRadiusM, safetyMarginM);
  const points = [];

  for (let i = 0; i < numUavs; i++) {
    const distanceM = i * spacing;
    const [pointLat, pointLon] =
      i === 0 ? [lat, lon] : destinationPoint(lat, lon, bearingDeg, distanceM);
    points.push({ index: i + 1, lat: pointLat, lon: pointLon, distanceM });
  }

  return points;
}

/**
 * A closed ring of [lon, lat] pairs approximating the loiter circle of
 * `radiusM` around (lat, lon).
 *
 * Built geodesically from the same `destinationPoint` the layout uses, so
 * the drawn circle and the drawn spacing come from one consistent model and
 * the gap between neighbours reads true at any latitude. The swarm computer
 * synthesizes only 8 ring points; this uses many more purely so the preview
 * looks like a circle rather than an octagon.
 */
export function loiterCircleRing(lat, lon, radiusM, segments = 72) {
  const ring = [];

  for (let i = 0; i <= segments; i++) {
    // i === segments repeats bearing 0 to close the ring.
    const [pointLat, pointLon] = destinationPoint(
      lat,
      lon,
      (360 * i) / segments,
      radiusM
    );
    ring.push([pointLon, pointLat]);
  }

  return ring;
}

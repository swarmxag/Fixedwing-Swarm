/**
 * @file Pure helpers for the unsafe-terrain areas that Xag-Server sends in
 * `X-TERRAIN-UNSAFE-AREA-RESP` messages (Step 4B of the terrain safety system).
 *
 * The server sends, per unsafe area, a closed `polygon` ring and optional
 * `holes` rings, all as `[lat, lon]` pairs. This file validates such a message
 * (a malformed area is skipped instead of breaking the map) and converts an
 * area into the `[x, y]` rings that OpenLayers expects. It has no dependency on
 * React, Redux or OpenLayers so it can be tested on its own.
 */

/** A `[lat, lon]` pair, as sent by the server. */
export type LatLon = [number, number];

export type UnsafeTerrainPoint = {
  lat: number;
  lon: number;
  elevation: number;
};

/** How to draw an already-unsafe area; computed by the SERVER (Xag-Server's
 * `terrain_areas.attach_area_severity`), never recomputed on the frontend. */
export type AreaSeverity = 'red' | 'yellow';

export type UnsafeArea = {
  id: number;
  cellCount: number;
  maxElevation: number;
  highestPoint: UnsafeTerrainPoint | undefined;
  /** Exterior ring, closed (first point repeated at the end) */
  polygon: LatLon[];
  /** Interior rings (safe pockets inside the area), each closed */
  holes: LatLon[][];
  /**
   * Colour the server wants this area drawn in, right now: RED while the
   * live UAV is still below this area's terrain, YELLOW once it has
   * reached/passed it but not yet cleared the safety margin. `undefined`
   * (an older server) means "draw plain red", the behaviour from before this
   * field existed -- the frontend never falls back to computing it itself.
   */
  severity: AreaSeverity | undefined;
};

export type UnsafeTerrainStatus = 'unsafe' | 'safe' | 'unavailable';

export type UnsafeTerrain = {
  status: UnsafeTerrainStatus;
  thresholdAMSL: number | undefined;
  areaCount: number;
  unsafeCellCount: number;
  maxUnsafeElevation: number | undefined;
  highestPoint: UnsafeTerrainPoint | undefined;
  areas: UnsafeArea[];
  originFingerprint: string | undefined;
  /** The UAV whose safety threshold this result is for; undefined = the Origin default */
  thresholdUavId: string | undefined;
  altitudeSource: string | undefined;

  /**
   * What the server calculated `thresholdAMSL` from:
   *   thresholdAMSL = referenceTerrainElevation + safetyAltitude - safetyMargin
   * The GCS only DISPLAYS these; the server is the one place that calculates.
   */
  referenceTerrainElevation: number | undefined; // home terrain, m AMSL
  safetyAltitude: number | undefined; // drone height, m
  safetyMargin: number | undefined; // positive distance that is subtracted, m

  /**
   * Where the home terrain elevation was read: at a UAV's own home
   * (`uav_home`), at the lowest home of all UAVs (`swarm_home`), or -- while no
   * UAV position is known -- at the corner of the Origin area (`origin_corner`).
   */
  referenceSource: string | undefined;
  referenceLocation: { lat: number; lon: number } | undefined;
};

const STATUSES = new Set<string>(['unsafe', 'safe', 'unavailable']);

const isNumber = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);

/** What may arrive over the wire: every field optional and untrusted. */
type RawPoint = { lat?: unknown; lon?: unknown; elevation?: unknown };
type RawArea = {
  id?: unknown;
  cellCount?: unknown;
  maxElevation?: unknown;
  highestPoint?: unknown;
  polygon?: unknown;
  holes?: unknown;
  severity?: unknown;
};
type RawMessage = {
  status?: unknown;
  thresholdAMSL?: unknown;
  unsafeCellCount?: unknown;
  maxUnsafeElevation?: unknown;
  highestPoint?: unknown;
  areas?: unknown;
  originFingerprint?: unknown;
  thresholdUavId?: unknown;
  altitudeSource?: unknown;
  referenceTerrainElevation?: unknown;
  safetyAltitude?: unknown;
  safetyMargin?: unknown;
  referenceSource?: unknown;
  referenceLocation?: unknown;
};

/** The value as an object of the given (untrusted) shape, or `undefined`. */
const asRaw = <T extends Record<string, unknown>>(
  value: unknown
): T | undefined =>
  typeof value === 'object' && value !== null ? (value as T) : undefined;

const numberOrUndefined = (value: unknown): number | undefined =>
  isNumber(value) ? value : undefined;

const stringOrUndefined = (value: unknown): string | undefined =>
  typeof value === 'string' ? value : undefined;

function parseLocation(
  value: unknown
): { lat: number; lon: number } | undefined {
  const raw = asRaw<{ lat?: unknown; lon?: unknown }>(value);
  return raw && isNumber(raw.lat) && isNumber(raw.lon)
    ? { lat: raw.lat, lon: raw.lon }
    : undefined;
}

function parsePoint(value: unknown): UnsafeTerrainPoint | undefined {
  const raw = asRaw<RawPoint>(value);
  if (
    raw &&
    isNumber(raw.lat) &&
    isNumber(raw.lon) &&
    isNumber(raw.elevation)
  ) {
    return { lat: raw.lat, lon: raw.lon, elevation: raw.elevation };
  }

  return undefined;
}

/**
 * Returns the ring if it is a usable polygon ring (at least three points, every
 * point a finite `[lat, lon]` pair within the valid range), otherwise `null`.
 */
function parseRing(value: unknown): LatLon[] | undefined {
  if (!Array.isArray(value) || value.length < 3) {
    return undefined;
  }

  const ring: LatLon[] = [];
  for (const point of value) {
    if (
      !Array.isArray(point) ||
      point.length < 2 ||
      !isNumber(point[0]) ||
      !isNumber(point[1]) ||
      Math.abs(point[0]) > 90 ||
      Math.abs(point[1]) > 180
    ) {
      return undefined;
    }

    ring.push([point[0], point[1]]);
  }

  return ring;
}

function parseArea(value: unknown, fallbackId: number): UnsafeArea | undefined {
  const raw = asRaw<RawArea>(value);
  if (!raw) {
    return undefined;
  }

  const polygon = parseRing(raw.polygon);
  if (!polygon) {
    return undefined;
  }

  const holes: LatLon[][] = [];
  if (Array.isArray(raw.holes)) {
    for (const hole of raw.holes) {
      const ring = parseRing(hole);
      if (ring) {
        holes.push(ring);
      }
    }
  }

  return {
    id: isNumber(raw.id) ? raw.id : fallbackId,
    cellCount: numberOrUndefined(raw.cellCount) ?? 0,
    maxElevation: numberOrUndefined(raw.maxElevation) ?? Number.NaN,
    highestPoint: parsePoint(raw.highestPoint),
    polygon,
    holes,
    severity:
      raw.severity === 'red' || raw.severity === 'yellow'
        ? raw.severity
        : undefined,
  };
}

/**
 * Validates and normalizes the body of an `X-TERRAIN-UNSAFE-AREA-RESP`
 * notification or response. Returns `undefined` if it is not such a message.
 * Areas whose polygon is unusable are dropped; the rest are kept.
 */
export function parseUnsafeTerrainMessage(
  body: unknown
): UnsafeTerrain | undefined {
  const raw = asRaw<RawMessage>(body);
  if (!raw || !STATUSES.has(raw.status as string)) {
    return undefined;
  }

  const status = raw.status as UnsafeTerrainStatus;
  const areas: UnsafeArea[] = [];
  if (status === 'unsafe' && Array.isArray(raw.areas)) {
    for (const [index, item] of raw.areas.entries()) {
      const area = parseArea(item, index + 1);
      if (area) {
        areas.push(area);
      }
    }
  }

  return {
    status,
    thresholdAMSL: numberOrUndefined(raw.thresholdAMSL),
    areaCount: areas.length,
    unsafeCellCount: numberOrUndefined(raw.unsafeCellCount) ?? 0,
    maxUnsafeElevation: numberOrUndefined(raw.maxUnsafeElevation),
    highestPoint: parsePoint(raw.highestPoint),
    areas,
    originFingerprint: stringOrUndefined(raw.originFingerprint),
    thresholdUavId: stringOrUndefined(raw.thresholdUavId),
    altitudeSource: stringOrUndefined(raw.altitudeSource),
    referenceTerrainElevation: numberOrUndefined(raw.referenceTerrainElevation),
    safetyAltitude: numberOrUndefined(raw.safetyAltitude),
    safetyMargin: numberOrUndefined(raw.safetyMargin),
    referenceSource: stringOrUndefined(raw.referenceSource),
    referenceLocation: parseLocation(raw.referenceLocation),
  };
}

/** Returns a copy of the ring that is closed (last point equals the first). */
function closed<T extends readonly number[]>(ring: T[]): T[] {
  const first = ring[0];
  const last = ring.at(-1);
  if (first && last && (first[0] !== last[0] || first[1] !== last[1])) {
    return [...ring, first];
  }

  return ring;
}

/**
 * Converts an area into the rings OpenLayers wants: `[exterior, ...holes]`,
 * every point an `[x, y]` pair produced by `project(lon, lat)` (note the order:
 * the server sends `[lat, lon]`, map projections take longitude first).
 */
export function areaToRings(
  area: UnsafeArea,
  project: (lonLat: [number, number]) => [number, number]
): Array<Array<[number, number]>> {
  const convert = (ring: readonly LatLon[]): Array<[number, number]> =>
    closed(ring.map(([lat, lon]) => project([lon, lat])));

  return [convert(area.polygon), ...area.holes.map(convert)];
}

/** A number of metres for display: whole numbers as they are, others with one decimal. */
const formatMetres = (value: number): string =>
  Number.isInteger(value) ? String(value) : value.toFixed(1);

/** One-line summary for the map widget. */
export function describeUnsafeTerrain(terrain: UnsafeTerrain): string {
  const threshold =
    terrain.thresholdAMSL === undefined
      ? ''
      : ` ${formatMetres(terrain.thresholdAMSL)} m AMSL`;

  switch (terrain.status) {
    case 'unsafe': {
      const highest =
        terrain.maxUnsafeElevation === undefined
          ? ''
          : `, highest ${terrain.maxUnsafeElevation.toFixed(0)} m`;
      const plural = terrain.areas.length === 1 ? 'area' : 'areas';
      return `Terrain above${threshold}: ${terrain.areas.length} ${plural}${highest}`;
    }

    case 'safe':
      return `No terrain above${threshold}`;

    default:
      return 'Terrain safety unavailable';
  }
}

/** Shown for a number that the server has not (yet) provided. */
const NO_VALUE = '—'; // em dash

/** The numbers behind the safety threshold, ready to show. */
export type ThresholdBreakdown = {
  homeTerrain: string;
  /** Where the home terrain was read, e.g. `UAV 01 home (30.8025, 79.8148)` */
  homeSource: string | undefined;
  droneHeight: string;
  safetyMargin: string;
  threshold: string;
  /** e.g. `300 + 100 - 50 = 350 m AMSL` */
  formula: string;

  /**
   * The highest terrain peak, taken as-is from the server's own
   * `maxUnsafeElevation` (Step 4A/4B) -- never recomputed here. An AMSL
   * elevation, like `homeTerrain` and `threshold`. `NO_VALUE` while the server
   * has not reported any unsafe terrain (status `safe` or `unavailable`).
   */
  highestPeak: string;

  /**
   * Height the drone needs above its home to clear the highest peak by the
   * safety margin:  highestPeak - homeTerrain + safetyMargin. Unlike
   * `threshold`, this is a RELATIVE height (like `droneHeight`), not an AMSL
   * elevation -- it has no ` AMSL` suffix, on purpose. `NO_VALUE` when
   * `highestPeak` is unavailable.
   */
  droneSafeAltitude: string;

  /** e.g. `425 - 300 + 50 = 175 m`; `undefined` when `highestPeak` is unavailable. */
  safeAltitudeFormula: string | undefined;
};

/** Says whose home (and where) the home terrain elevation was read at. */
function describeHomeSource(terrain: UnsafeTerrain): string | undefined {
  const { referenceSource, referenceLocation, thresholdUavId } = terrain;
  const where = referenceLocation
    ? ` (${referenceLocation.lat.toFixed(4)}, ${referenceLocation.lon.toFixed(4)})`
    : '';
  switch (referenceSource) {
    case 'uav_home':
      return `${thresholdUavId ? `UAV ${thresholdUavId}` : 'UAV'} home${where}`;
    case 'swarm_home':
      return `lowest UAV home${where}`;
    case 'origin_corner':
      return `Origin corner${where}, no UAV position yet`;
    default:
      return undefined;
  }
}

/**
 * Formats the inputs of the server's safety threshold for display. Nothing is
 * calculated here: the threshold shown is the one the server sent, even if it
 * were not the sum of the other numbers. Returns `undefined` when the server did
 * not send all of them (e.g. an older server).
 */
export function describeThresholdBreakdown(
  terrain: UnsafeTerrain
): ThresholdBreakdown | undefined {
  const {
    referenceTerrainElevation,
    safetyAltitude,
    safetyMargin,
    thresholdAMSL,
  } = terrain;
  if (
    referenceTerrainElevation === undefined ||
    safetyAltitude === undefined ||
    safetyMargin === undefined ||
    thresholdAMSL === undefined
  ) {
    return undefined;
  }

  const home = formatMetres(referenceTerrainElevation);
  const height = formatMetres(safetyAltitude);
  const margin = formatMetres(safetyMargin);
  const threshold = formatMetres(thresholdAMSL);

  // Highest terrain peak: the server's own Step 4A/4B maxUnsafeElevation, used
  // as-is (never recomputed) -- see droneSafeAltitude below, the ONE place that
  // combines it with the threshold inputs.
  const { maxUnsafeElevation } = terrain;
  const highestPeakKnown = maxUnsafeElevation !== undefined;
  const highestPeak = highestPeakKnown
    ? `${formatMetres(maxUnsafeElevation)} m AMSL`
    : NO_VALUE;

  // Drone safe altitude = highestPeak - homeTerrain + safetyMargin: the height
  // above home that clears the highest peak by the safety margin. A relative
  // height (no " AMSL"), unlike `threshold`.
  const droneSafeAltitudeValue = highestPeakKnown
    ? maxUnsafeElevation - referenceTerrainElevation + safetyMargin
    : undefined;
  const droneSafeAltitude =
    droneSafeAltitudeValue === undefined
      ? NO_VALUE
      : `${formatMetres(droneSafeAltitudeValue)} m`;
  const safeAltitudeFormula =
    droneSafeAltitudeValue === undefined
      ? undefined
      : `${formatMetres(maxUnsafeElevation!)} - ${home} + ${margin} = ${formatMetres(droneSafeAltitudeValue)} m`;

  return {
    homeTerrain: `${home} m AMSL`,
    homeSource: describeHomeSource(terrain),
    droneHeight: `${height} m`,
    safetyMargin: `${margin} m`,
    threshold: `${threshold} m AMSL`,
    formula: `${home} + ${height} - ${margin} = ${threshold} m AMSL`,
    highestPeak,
    droneSafeAltitude,
    safeAltitudeFormula,
  };
}

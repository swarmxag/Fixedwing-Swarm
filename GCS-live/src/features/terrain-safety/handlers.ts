/**
 * @file Handling of the server's unsafe-terrain messages. Kept free of any
 * import of the message hub, because the message hub imports this file to
 * register the notification handler (see `request.ts` for the other direction).
 */

import { type Dispatch } from '@reduxjs/toolkit';

import { parseUnsafeTerrainMessage } from './areas';
import { setUnsafeTerrain } from './slice';

// ===== TEMP-TERRAIN-TRACE (temporary diagnostics; delete this whole block and its one call below) =====
// Records, for every X-TERRAIN-UNSAFE-AREA-RESP the GCS receives, what the SERVER sent (`raw`) and what
// this file is about to put into Redux (`parsed`). Read it in DevTools with:
//   copy(JSON.stringify(window.__terrainTrace, null, 1))
type TraceArea = { id: unknown; severity: unknown; maxElevation: unknown };
type LooseArea = { id?: unknown; severity?: unknown; maxElevation?: unknown };
type LooseBody = {
  status?: unknown;
  thresholdAMSL?: unknown;
  safetyAltitude?: unknown;
  referenceTerrainElevation?: unknown;
  safetyMargin?: unknown;
  thresholdUavId?: unknown;
  altitudeSource?: unknown;
  areas?: unknown;
};

const summarizeAreas = (areas: unknown): TraceArea[] =>
  Array.isArray(areas)
    ? areas.map((a: LooseArea | null) => ({
        id: a?.id,
        severity: a?.severity,
        maxElevation: a?.maxElevation,
      }))
    : [];

function traceTerrainMessage(body: unknown, parsed: unknown): void {
  const raw = (body ?? {}) as LooseBody;
  const out = (parsed ?? {}) as LooseBody;
  const entry = {
    at: new Date().toISOString(),
    status: raw.status,
    thresholdAMSL: raw.thresholdAMSL,
    safetyAltitude: raw.safetyAltitude,
    referenceTerrainElevation: raw.referenceTerrainElevation,
    safetyMargin: raw.safetyMargin,
    thresholdUavId: raw.thresholdUavId,
    altitudeSource: raw.altitudeSource,
    raw: summarizeAreas(raw.areas),
    parsed: summarizeAreas(out.areas),
  };
  const w = window as unknown as { __terrainTrace?: unknown[] };
  w.__terrainTrace = [...(w.__terrainTrace ?? []).slice(-199), entry];
  console.log('[TERRAIN-TRACE] RECEIVED TERRAIN AREA UPDATE', entry);
}
// ===== end TEMP-TERRAIN-TRACE =====

/**
 * Handles the body of an `X-TERRAIN-UNSAFE-AREA-RESP` notification or response.
 * A message that does not look like one is ignored (with a console warning), so
 * a bad message can never blank or break the map.
 */
export function handleUnsafeTerrainMessage(
  body: unknown,
  dispatch: Dispatch
): void {
  const unsafeTerrain = parseUnsafeTerrainMessage(body);
  traceTerrainMessage(body, unsafeTerrain); // TEMP-TERRAIN-TRACE: remove with its definition below
  if (unsafeTerrain) {
    dispatch(setUnsafeTerrain(unsafeTerrain));
  } else {
    console.warn('Ignoring malformed X-TERRAIN-UNSAFE-AREA-RESP message', body);
  }
}

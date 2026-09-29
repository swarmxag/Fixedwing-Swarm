/**
 * @file Handling of the server's unsafe-terrain messages. Kept free of any
 * import of the message hub, because the message hub imports this file to
 * register the notification handler (see `request.ts` for the other direction).
 */

import { type Dispatch } from '@reduxjs/toolkit';

import { parseUnsafeTerrainMessage } from './areas';
import { setUnsafeTerrain } from './slice';

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
  if (unsafeTerrain) {
    dispatch(setUnsafeTerrain(unsafeTerrain));
  } else {
    console.warn('Ignoring malformed X-TERRAIN-UNSAFE-AREA-RESP message', body);
  }
}

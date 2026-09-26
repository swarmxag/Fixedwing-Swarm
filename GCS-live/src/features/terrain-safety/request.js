/**
 * @file Asks the server for the current unsafe terrain areas.
 *
 * The server broadcasts `X-TERRAIN-UNSAFE-AREA-RESP` whenever the safety
 * threshold changes, but a GCS that connects (or reconnects) afterwards has
 * missed the last broadcast; this read-only request fetches the current state.
 */

import messageHub from '~/message-hub';

import { handleUnsafeTerrainMessage } from './handlers';

/**
 * @param {Function} dispatch  the Redux dispatch function
 * @returns {Promise<void>}
 */
export async function requestUnsafeTerrain(dispatch) {
  try {
    const response = await messageHub.sendMessage(
      { type: 'X-TERRAIN-UNSAFE-AREA-REQ' },
      // the server answers from memory (no SRTM, no grid rebuild)
      { timeout: 10 }
    );
    handleUnsafeTerrainMessage(response?.body, dispatch);
  } catch (error) {
    // Best effort: an older server without terrain safety just does not answer.
    console.warn('Could not fetch the unsafe terrain areas:', error);
  }
}

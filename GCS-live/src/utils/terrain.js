/**
 * @file Utility for fetching and caching terrain elevation via Socket.IO.
 */

import messageHub from '~/message-hub';

const elevationCache = new Map();
const pendingKeys = new Set();
const listeners = new Set();

/**
 * Upper bound on cached cells. A Map preserves insertion order, so the oldest
 * key is always the first one -- evicting it gives LRU-by-insertion without a
 * second data structure. An evicted cell simply re-queries on the next hover,
 * so the only cost of eviction is one extra round trip.
 *
 * Without a cap this grows one entry per ~100 m cell for as long as the session
 * lasts, which over a wide area is unbounded.
 */
const MAX_CACHED_CELLS = 5000;

function cacheElevation(key, entry) {
  // Re-inserting must move the key to the newest position, so delete first.
  elevationCache.delete(key);
  elevationCache.set(key, entry);

  while (elevationCache.size > MAX_CACHED_CELLS) {
    const oldest = elevationCache.keys().next();
    if (oldest.done) {
      break;
    }

    elevationCache.delete(oldest.value);
  }
}

/**
 * Registers a listener to be notified whenever new terrain elevation data arrives.
 * @param {Function} listener
 * @returns {Function} Unsubscribe callback
 */
export function subscribeTerrainUpdates(listener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function flushListeners() {
  for (const listener of listeners) {
    try {
      listener();
    } catch (error) {
      console.error('Terrain update listener error:', error);
    }
  }
}

/**
 * Coalesces notifications into at most one per frame.
 *
 * Every resolved lookup used to notify immediately, and the map's only way to
 * refresh the readout is to remount its MousePosition control (its `key`
 * changes) -- so sweeping the mouse over N uncached cells produced N remounts.
 * Batching collapses a burst into a single one, which is all the UI needs since
 * the readout shows one coordinate at a time.
 */
let notifyScheduled = false;

function notifyListeners() {
  if (notifyScheduled || listeners.size === 0) {
    return;
  }

  notifyScheduled = true;

  const run = () => {
    notifyScheduled = false;
    flushListeners();
  };

  // rAF keeps this aligned with painting; it does not fire in a background tab,
  // so fall back to a timer where it is unavailable.
  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(run);
  } else {
    setTimeout(run, 16);
  }
}

/**
 * Drops every cached "no data" result (a hover lookup that resolved to
 * null, or failed, before its tile was downloaded) so the next hover over
 * those grid cells re-queries the server instead of replaying the stale
 * miss forever. Resolved entries with a real elevation are left alone --
 * only unresolved/negative ones are invalidated.
 *
 * Called after a "Set Origin" range download actually fetches new tiles:
 * without this, any cell hovered before/during that download would show
 * "Elev: N/A" for the rest of the session even though the data now exists.
 */
function clearStaleNegativeCache() {
  let cleared = false;
  for (const [key, entry] of elevationCache) {
    if (
      entry.status !== 'pending' &&
      (entry.elevation === null || entry.elevation === undefined)
    ) {
      elevationCache.delete(key);
      cleared = true;
    }
  }

  if (cleared) {
    notifyListeners();
  }
}

/**
 * Requests elevation for one grid cell from Xag-Server via Socket.IO.
 *
 * Not debounced: a single shared debounce here would only keep the
 * *last* call's arguments, so sweeping the mouse across several new
 * (not-yet-cached) points within the debounce window would silently drop
 * every earlier point's request -- it would stay marked "pending" in the
 * cache forever with nothing ever fetching it. Deduplication is instead
 * handled per-key: `getElevationFormatted` only calls this once per key
 * (it returns early for a key that's already in the cache), and
 * `pendingKeys` below is a belt-and-suspenders guard against firing twice
 * for the same key concurrently.
 */
const requestElevation = async (key, lat, lon) => {
  if (pendingKeys.has(key)) {
    return;
  }

  pendingKeys.add(key);

  try {
    const response = await messageHub.sendMessage(
      {
        type: 'X-TERRAIN-REQ',
        lat,
        lon,
      },
      // The server downloads a missing tile before answering, so this has to
      // outlast a ~26 MB download, not just a round trip.
      { timeout: 60 }
    );

    const body = response ? response.body : {};
    const elevation =
      body && body.elevation !== undefined ? body.elevation : null;

    cacheElevation(key, {
      status: 'resolved',
      elevation,
    });
  } catch (error) {
    console.warn(`[Terrain] Socket.IO request failed for ${key}:`, error);
    cacheElevation(key, {
      status: 'failed',
      elevation: null,
    });
  } finally {
    pendingKeys.delete(key);
    notifyListeners();
  }
};

/**
 * Pre-fetches every SRTM tile covering the bounding box of `points`
 * (e.g. the geofence polygon submitted with "Set Origin"), so that later
 * hover lookups in that area resolve from the local cache instead of each
 * triggering their own lazy per-point download.
 *
 * Fire-and-forget from the caller's point of view: this awaits the server
 * response internally (it never throws), but the "downloading" / "download
 * completed" indication the user sees is a SYS-MSG notification pushed by
 * the server independently of this request, so the caller doesn't need to
 * do anything with the return value to get that feedback.
 *
 * @param {Array<Array<number>>} points [lon, lat] pairs
 * @returns {Promise<object|null>} the response body, or null on failure
 */
export async function requestTerrainRange(points) {
  if (!Array.isArray(points) || points.length === 0) {
    console.warn('[Terrain] Range request skipped -- no points given', points);
    return null;
  }

  console.log(
    `[Terrain] Requesting terrain range for ${points.length} point(s)`,
    points
  );

  try {
    const response = await messageHub.sendMessage(
      {
        type: 'X-TERRAIN-RANGE-REQ',
        points,
      },
      { timeout: 180 } // Bulk downloads of several tiles can take a while
    );
    const body = response ? response.body : null;
    console.log('[Terrain] Range request response:', body);

    if (
      body &&
      body.status === 'completed' &&
      body.downloaded_tiles?.length > 0
    ) {
      clearStaleNegativeCache();
    }

    return body;
  } catch (error) {
    console.warn('[Terrain] Range request failed:', error);
    return null;
  }
}

/**
 * Formats the terrain elevation for the given coordinate [lon, lat].
 * Returns "Elev: XXX m", "Elev: ---" (while waiting), or "Elev: N/A".
 *
 * @param {Array<number>} coords [longitude, latitude]
 * @returns {string} Formatted elevation string
 */
export function getElevationFormatted(coords) {
  if (!coords || coords.length < 2) {
    return 'Elev: N/A';
  }

  const [lon, lat] = coords;
  if (
    typeof lat !== 'number' ||
    typeof lon !== 'number' ||
    Number.isNaN(lat) ||
    Number.isNaN(lon)
  ) {
    return 'Elev: N/A';
  }

  // Grid resolution key: 3 decimal places (~100m grid cell)
  const key = `${lat.toFixed(3)},${lon.toFixed(3)}`;
  const entry = elevationCache.get(key);

  if (entry) {
    if (entry.status === 'pending') {
      return 'Elev: ---';
    }

    if (entry.elevation === null || entry.elevation === undefined) {
      return 'Elev: N/A';
    }

    return `Elev: ${Math.round(entry.elevation)} m`;
  }

  // Not in cache yet: mark pending and queue request
  cacheElevation(key, { status: 'pending', elevation: null });
  requestElevation(key, lat, lon);

  return 'Elev: ---';
}

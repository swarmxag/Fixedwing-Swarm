/**
 * @file What a takeoff needs from the operator: the marker the first guided
 * points are generated from, the takeoff height and the height difference.
 * Pure code so that it can be tested without React.
 */

/** ID of the marker takeoff uses: the first marker placed gets this ID. */
export const TAKEOFF_MARKER_ID = 'marker';

/** Colour of that marker on the map and in the feature list. */
export const TAKEOFF_MARKER_COLOR = '#f44336';

type MarkerLike = {
  id?: string;
  type?: string;
  visible?: boolean;
  points?: readonly unknown[];
};

export const isTakeoffMarker = (feature?: MarkerLike): boolean =>
  feature?.id === TAKEOFF_MARKER_ID && feature?.type === 'points';

/**
 * Returns why a takeoff must not be sent, or null if it can be. A marker hidden
 * from the map counts as missing so that UAVs never head for a point the
 * operator cannot see.
 */
export const getTakeoffProblem = (
  marker: MarkerLike | undefined,
  takeoffAlt: unknown,
  takeoffAltDiff: unknown
): string | null => {
  if (!isTakeoffMarker(marker) || !marker?.visible || !marker.points?.length) {
    return 'Takeoff not sent: no takeoff marker. Place a marker on the map first.';
  }

  if (!Number.isFinite(takeoffAlt) || (takeoffAlt as number) <= 0) {
    return 'Takeoff not sent: enter the takeoff height.';
  }

  if (!Number.isFinite(takeoffAltDiff) || (takeoffAltDiff as number) < 0) {
    return 'Takeoff not sent: enter the height difference (0 or more).';
  }

  return null;
};

import { type RootState } from '~/store/reducers';

import { type UnsafeTerrain } from './areas';

/** The latest unsafe-terrain result from the server, if any. */
export const getUnsafeTerrain = (state: RootState): UnsafeTerrain | undefined =>
  state.terrainSafety.unsafeTerrain as UnsafeTerrain | undefined;

/** Whether the unsafe areas are currently shown on the map. */
export const isUnsafeTerrainVisible = (state: RootState): boolean =>
  state.terrainSafety.visible;

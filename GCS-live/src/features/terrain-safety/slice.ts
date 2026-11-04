/**
 * @file Slice of the state object that holds the unsafe terrain areas reported
 * by the server (terrain above the current safety threshold, Step 4B) and
 * whether they are shown on the map.
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { type ReadonlyDeep } from 'type-fest';

import { type UnsafeTerrain } from './areas';

type TerrainSafetySliceState = ReadonlyDeep<{
  /** Whether the red unsafe areas are drawn on the map (a user preference) */
  visible: boolean;

  /**
   * The latest result received from the server; `undefined` until the first one
   * arrives and after the server reports that terrain safety is unavailable.
   */
  unsafeTerrain: UnsafeTerrain | undefined;
}>;

const initialState: TerrainSafetySliceState = {
  visible: true,
  unsafeTerrain: undefined,
};

const { actions, reducer } = createSlice({
  name: 'terrainSafety',
  initialState,
  reducers: {
    /** Stores a result from the server. "Unavailable" clears it (no Origin, no threshold, ...). */
    setUnsafeTerrain(state, action: PayloadAction<UnsafeTerrain>) {
      state.unsafeTerrain =
        action.payload.status === 'unavailable' ? undefined : action.payload;
    },

    clearUnsafeTerrain(state) {
      state.unsafeTerrain = undefined;
    },

    setUnsafeTerrainVisible(state, action: PayloadAction<boolean>) {
      state.visible = action.payload;
    },
  },
});

export const { setUnsafeTerrain, clearUnsafeTerrain, setUnsafeTerrainVisible } =
  actions;

export default reducer;

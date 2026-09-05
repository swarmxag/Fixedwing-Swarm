/**
 * @file Reducer function for handling the center, zoom level and rotation of
 * the map.
 *
 * Due to how OpenLayers works, we cannot make the Redux store the single source
 * of truth for the center, zoom level and rotation of the map. When the map
 * view is visible, the view manages its own center, zoom level and rotation,
 * and dispatches actions to update the stored center, zoom level and rotation
 * in the store whenever the user finished moving the map. When the map view
 * is not visible, the Redux store is the source of the truth. When the map view
 * is mounted for the first time, it is initialized from the state of the store.
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { type ReadonlyDeep } from 'type-fest';

/**
 * The state of the origin (home position) and the global flat Earth coordinate
 * system of the map.
 *
 * The flat Earth coordinate system is at the given position and its zero
 * degree heading points towards the heading given in the `angle` property.
 */
type autopanSlice = ReadonlyDeep<{
  uavid: string;
  isAutoPan: boolean;
}>;

const initialState: autopanSlice = {
  uavid: '',
  isAutoPan: false,
};

const { actions, reducer } = createSlice({
  name: 'map/view',
  initialState,
  reducers: {
    updateAutoPanSettings(
      state,
      action: PayloadAction<{
        uavid: string;
        isAutoPan: boolean;
      }>
    ) {
      state.uavid = action.payload.uavid;
      state.isAutoPan = action.payload.isAutoPan;
    },

    stopAutoPan(state) {
      state.isAutoPan = false;
      state.uavid = '';
    },
  },
});

export const { updateAutoPanSettings, stopAutoPan } = actions;

export default reducer;

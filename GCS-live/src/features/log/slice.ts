/**
 * @file Slice of the state object that handles the contents of the log window.
 */

import isNil from 'lodash-es/isNil';
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { type ReadonlyDeep } from 'type-fest';

import { type LogItem, type FileItem } from './types';

type LogSliceState = ReadonlyDeep<{
  highestUnseenMessageLevel: number;
  items: LogItem[];
  nextId: number;
  panelVisible: boolean;
  socketItems: FileItem[];
}>;

const initialState: LogSliceState = {
  highestUnseenMessageLevel: -1,
  items: [],
  socketItems: [],
  nextId: 0,
  panelVisible: false,
};

const { actions, reducer } = createSlice({
  name: 'log',
  initialState,
  reducers: {
    addLogItem(state, action: PayloadAction<Partial<Omit<LogItem, 'id'>>>) {
      const { auxiliaryId, message, module, level, timestamp } = action.payload;
      const newItem = {
        id: state.nextId,
        timestamp: isNil(timestamp) ? Date.now() : timestamp,
        message: message ?? '',
        module: module ?? '',
        level: level ?? 0,
        auxiliaryId: auxiliaryId ?? '',
      };

      state.items.push(newItem);
      state.nextId += 1;

      if (!state.panelVisible && level !== undefined) {
        state.highestUnseenMessageLevel = Math.max(
          state.highestUnseenMessageLevel,
          level
        );
      }
    },

    addTextLog(state, action: PayloadAction<FileItem[]>) {
      state.socketItems = action.payload;
    },

    clearLogItems(state) {
      state.items = [];
      state.highestUnseenMessageLevel = -1;
    },

    deleteLogItem(state, action: PayloadAction<number>) {
      const deletedItemId = action.payload;
      const index = state.items.findIndex((item) => item.id === deletedItemId);
      if (index >= 0) {
        state.items.splice(index, 1);
      }
    },

    updateLogPanelVisibility(state, action: PayloadAction<boolean>) {
      state.panelVisible = Boolean(action.payload);

      if (state.panelVisible) {
        state.highestUnseenMessageLevel = -1;
      }
    },
  },
});

export const {
  addLogItem,
  clearLogItems,
  deleteLogItem,
  updateLogPanelVisibility,
  addTextLog,
} = actions;

export default reducer;

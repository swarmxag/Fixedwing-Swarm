import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export type ControlSliceState = {
  totalrvt: number[];
  accessgranded: number[];
  notAccess: number[];
};

const initialState: ControlSliceState = {
  totalrvt: [],
  accessgranded: [],
  notAccess: [],
};

const { actions, reducer } = createSlice({
  name: 'requestcontrol',
  initialState,
  reducers: {
    requestAccess(state, action: PayloadAction<number>) {
      state.accessgranded.push(action.payload);
      let result = state.totalrvt.filter(
        (num) => !state.accessgranded.includes(num)
      );
      state.notAccess = result;
    },
    cancelRequest(state, action: PayloadAction<number>) {
      let updatedNumbers = state.accessgranded.filter(
        (num) => num !== action.payload
      );
      state.accessgranded = updatedNumbers;
    },
  },
});

export const {} = actions;

export default reducer;

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { nanoid } from 'nanoid';

type targetType = {
  lat: number;
  lon: number;
  id: string;
};

type targetCNFType = {
  target: targetType[] | [];
  status1: string[] | [];
  status2: string[] | [];
  armed: boolean;
  DET: boolean;
  health: boolean;
  charging: boolean;
};

const initialState: targetCNFType = {
  target: [],
  status1: [],
  status2: [],
  armed: false,
  DET: false,
  health: false,
  charging: false,
};

const { actions, reducer } = createSlice({
  name: 'targetCNF',
  initialState,
  reducers: {
    addtargetCNF(state, action: PayloadAction<Omit<targetType, 'id'>>) {
      const tar = { ...action.payload, id: nanoid(10) } as targetType;
      (state.target as targetType[]).push(tar);
    },
    removetargetCNF(state, action: PayloadAction<string>) {
      state.target = state.target.filter(
        (target) => target.id !== action.payload
      );
    },
    updateStatus1Sdal(state, action: PayloadAction<string[]>) {
      state.status1 = action.payload;
    },
    updateStatus2Sdal(state, action: PayloadAction<string[]>) {
      state.status2 = action.payload;
    },
    updateArmedStatus(state, action: PayloadAction<boolean>) {
      state.armed = action.payload;
    },
    updateDETStatus(state, action: PayloadAction<boolean>) {
      state.DET = action.payload;
    },
    updateHealth(state, action: PayloadAction<boolean>) {
      state.health = action.payload;
    },
    updateChargingStatus(state, action: PayloadAction<boolean>) {
      state.charging = action.payload;
    },
  },
});

export const {
  addtargetCNF,
  removetargetCNF,
  updateStatus1Sdal,
  updateStatus2Sdal,
  updateArmedStatus,
  updateDETStatus,
  updateHealth,
  updateChargingStatus,
} = actions;

export default reducer;

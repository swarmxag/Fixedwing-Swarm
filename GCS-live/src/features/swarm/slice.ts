import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { noPayload } from '~/utils/redux';

type Group = {
  [k: string]: string[];
};
type MissionByUav = {
  [uavId: string]: Array<[number, number]>;
};

interface SwarmSlice {
  coverage: number;
  gridSpacing: number;
  Direction: string;
  skip_waypoint: number;
  radius: number;
  speed: number;
  groupsplitDialog: boolean;
  numOfGroups: number;
  group: Group;
  selectedTab: 'Create' | 'Delete' | 'View Groups';
  time: number;
  timerRunning: boolean;
  missionByUav: MissionByUav;
  baseAltitude: number;
  altitudeStep: number;
}

const initialState: SwarmSlice = {
  coverage: 500,
  gridSpacing: 50,
  Direction: 'ClockWise Direction',
  skip_waypoint: 0,
  radius: 0,
  speed: 18,
  groupsplitDialog: false,
  numOfGroups: 0,
  group: {},
  selectedTab: 'Create',
  time: 0,
  timerRunning: false,
  missionByUav: {},
  // Matches medur_fixed_wing.py's hardcoded different_height default
  // (base 300, spaced 10 apart) so the UI starts at the same values the
  // swarm computer already assumes before any "different" command is sent.
  baseAltitude: 300,
  altitudeStep: 10,
};

const { actions, reducer } = createSlice({
  name: 'socketswarm',
  initialState,
  reducers: {
    changeCoverage(state, action: PayloadAction<{ coverage: number }>) {
      state.coverage = action.payload.coverage;
    },
    changeGridSpacing(state, action: PayloadAction<{ gridSpacing: number }>) {
      state.gridSpacing = action.payload.gridSpacing;
    },
    changeDirection(state, action: PayloadAction<{ direction: string }>) {
      state.Direction = action.payload.direction;
    },
    changeWayPoint(state, action: PayloadAction<{ waypoint: number }>) {
      state.skip_waypoint = action.payload.waypoint;
    },
    changeRadius(state, action: PayloadAction<{ radius: number }>) {
      state.radius = action.payload.radius;
    },
    changeSpeed(state, action: PayloadAction<{ speed: number }>) {
      state.speed = action.payload.speed;
    },
    changeBaseAltitude(state, action: PayloadAction<{ baseAltitude: number }>) {
      state.baseAltitude = action.payload.baseAltitude;
    },
    changeAltitudeStep(state, action: PayloadAction<{ altitudeStep: number }>) {
      state.altitudeStep = action.payload.altitudeStep;
    },
    openGroupSplitDialog: noPayload<SwarmSlice>((state) => {
      state.groupsplitDialog = true;
    }),
    closeGroupSplitingDialog: noPayload<SwarmSlice>((state) => {
      state.groupsplitDialog = false;
    }),
    addGroup: (
      state,
      action: PayloadAction<{ id: string; uavs: string[] }>
    ) => {
      state.group[action.payload.id] = action.payload.uavs;
    },
    changeSelectedTab: (
      state,
      action: PayloadAction<SwarmSlice['selectedTab']>
    ) => {
      state.selectedTab = action.payload;
    },
    resetGroup: noPayload<SwarmSlice>((state) => {
      state.group = {};
    }),
    deleteGroup: (state, action: PayloadAction<string>) => {
      delete state.group[action.payload];
    },
    setTime: (state, actions: PayloadAction<number>) => {
      state.time = actions.payload;
    },
    setTimerRunning: (state, action: PayloadAction<boolean>) => {
      state.timerRunning = action.payload;
    },
    // Merges (not replaces) so a search response for UAV2 and a split
    // response for UAV1+UAV3 both stay on the map at once -- each only
    // overwrites the specific UAV ids present in its own payload, so a
    // UAV keeps showing its last route until it's actually given a new
    // command of its own.
    mergeMissionForUavs(state, action: PayloadAction<MissionByUav>) {
      state.missionByUav = { ...state.missionByUav, ...action.payload };
    },
    clearMissionByUav: noPayload<SwarmSlice>((state) => {
      state.missionByUav = {};
    }),
  },
});

export const {
  changeWayPoint,
  changeDirection,
  changeCoverage,
  changeGridSpacing,
  changeRadius,
  changeSpeed,
  changeBaseAltitude,
  changeAltitudeStep,
  openGroupSplitDialog,
  closeGroupSplitingDialog,
  addGroup,
  changeSelectedTab,
  resetGroup,
  setTime,
  setTimerRunning,
  mergeMissionForUavs,
  clearMissionByUav,
} = actions;

export default reducer;

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
  // "Automate Goals" strategy: operator drops ONE goal point and the swarm
  // computer fans it into one loiter centre per selected UAV, marching along
  // `automateBearing`, spaced 2*radius + `automateSafetyMargin` apart so the
  // loiter circles never overlap. Defaults mirror goal_point_generator.py
  // (DEFAULT_BEARING_DEG / DEFAULT_SAFETY_MARGIN_M).
  automateGoals: boolean;
  automateBearing: number;
  automateSafetyMargin: number;
  groupsplitDialog: boolean;
  numOfGroups: number;
  group: Group;
  selectedTab: 'Create' | 'Delete' | 'View Groups';
  time: number;
  timerRunning: boolean;
  missionByUav: MissionByUav;
  baseAltitude: number;
  altitudeStep: number;
  simPattern: string;
  simVehicle: 'copter' | 'plane';
  UAVRow: number;
  UAVColumn: number;
  UAVSpacing: number;
  NoOfUAVs: number;
}

const initialState: SwarmSlice = {
  coverage: 500,
  gridSpacing: 50,
  Direction: 'ClockWise Direction',
  skip_waypoint: 0,
  radius: 0,
  speed: 18,
  automateGoals: false,
  automateBearing: 90,
  automateSafetyMargin: 50,
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
  simPattern: 'Line',
  simVehicle: 'plane',
  NoOfUAVs: 1,
  UAVSpacing: 10,
  UAVRow: NaN,
  UAVColumn: NaN,
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
    setAutomateGoals(state, action: PayloadAction<{ automateGoals: boolean }>) {
      state.automateGoals = action.payload.automateGoals;
    },
    changeAutomateBearing(
      state,
      action: PayloadAction<{ automateBearing: number }>
    ) {
      state.automateBearing = action.payload.automateBearing;
    },
    changeAutomateSafetyMargin(
      state,
      action: PayloadAction<{ automateSafetyMargin: number }>
    ) {
      state.automateSafetyMargin = action.payload.automateSafetyMargin;
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
    changeNoUAVs(state, action: PayloadAction<{ NoOfUAVs: number }>) {
      state.NoOfUAVs = action.payload.NoOfUAVs;
    },
    changeUavSpacing(state, action: PayloadAction<{ UAVSpacing: number }>) {
      state.UAVSpacing = action.payload.UAVSpacing;
    },
    changeUavRow(state, action: PayloadAction<{ UAVRow: number }>) {
      state.UAVRow = action.payload.UAVRow;
    },
    changeUavColumn(state, action: PayloadAction<{ UAVColumn: number }>) {
      state.UAVColumn = action.payload.UAVColumn;
    },
    changeSimPattern(state, action: PayloadAction<{ simPattern: string }>) {
      state.simPattern = action.payload.simPattern;
    },
    changeSimVehicle(
      state,
      action: PayloadAction<{ simVehicle: SwarmSlice['simVehicle'] }>
    ) {
      state.simVehicle = action.payload.simVehicle;
    },
  },
});

export const {
  changeWayPoint,
  changeDirection,
  changeCoverage,
  changeGridSpacing,
  changeRadius,
  changeSpeed,
  setAutomateGoals,
  changeAutomateBearing,
  changeAutomateSafetyMargin,
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
  changeNoUAVs,
  changeUavSpacing,
  changeUavRow,
  changeUavColumn,
  changeSimPattern,
  changeSimVehicle,
} = actions;

export default reducer;

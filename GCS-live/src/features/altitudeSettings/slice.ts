import {createSlice, type PayloadAction} from '@reduxjs/toolkit';

interface AltitudeSettingsSlice {
    altitude: number;
    difference: number;
    data: {
        [key: string]: number;
    },
    initial:boolean;
    altitudes: number[] | [] | unknown[]
}

const initialState: AltitudeSettingsSlice = {
    altitude: 300,
    difference: 10,
    data:{},
    initial:true,
    altitudes:[]
}

const {actions, reducer} = createSlice({
    name: 'altitudeSettings',
    initialState,
    reducers: {
        changeAltitude(
            state,
            action: PayloadAction<{ altitude: number }>
        ) {
            state.altitude = action.payload.altitude;
        },
        changeDifference(
            state,
            action: PayloadAction<{ difference: number }>
        ) {
            state.difference = action.payload.difference;
        },
        changeAltitudesArray(state,action: PayloadAction<{ altitudes: number[] | unknown[] | [] }>) {
            state.altitudes = action.payload.altitudes;
        },
        changeSingeAltitude(state,action: PayloadAction<{ index:number,value: number }>) {
            const {index,value} = action.payload;
            if (index >= 0 && index < state.altitudes.length) {
                state.altitudes[index] = value;
            }
        },
        changeInitial(state) {
            state.initial = false;
        },
        changeInitialDataTonule(state) {
            state.data = {};
        },
        changeData(state,action: PayloadAction<{ index:string,value:number }>) {
            state.data[action.payload.index] = action.payload.value;
        }
    }
});

export const {changeAltitude,changeDifference,changeAltitudesArray,changeSingeAltitude,changeInitial,changeData,changeInitialDataTonule} = actions

export default reducer;

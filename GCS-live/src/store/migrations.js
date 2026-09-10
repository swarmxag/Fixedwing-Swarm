import { createNextState } from '@reduxjs/toolkit';
import { createMigrate } from 'redux-persist';

import {
  DEFAULT_BATTERY_CELL_COUNT,
  LIPO_CRITICAL_VOLTAGE_THRESHOLD,
  LIPO_FULL_CHARGE_VOLTAGE,
  LIPO_LOW_VOLTAGE_THRESHOLD,
} from '~/model/constants';

const migrations = {
  2: createNextState((state) => {
    state.settings.uavs = {
      ...state.settings.uavs,
      defaultBatteryCellCount: DEFAULT_BATTERY_CELL_COUNT,
      fullChargeVoltage: LIPO_FULL_CHARGE_VOLTAGE,
      lowVoltageThreshold: LIPO_LOW_VOLTAGE_THRESHOLD,
      criticalVoltageThreshold: LIPO_CRITICAL_VOLTAGE_THRESHOLD,
    };
  }),

  // `map` is not blacklisted, so map.selection is persisted -- which meant a
  // nil that got into the selection survived every restart and threw on each
  // launch, as soon as anything handed it to OpenLayers' getFeatureById
  // (implemented as `featureId.toString()`). updateSelection now keeps nils
  // out of the store, but that does nothing for a selection already written to
  // disk, so the stored copy is cleaned once here.
  3: createNextState((state) => {
    if (Array.isArray(state?.map?.selection)) {
      state.map.selection = state.map.selection.filter(
        (id) => id !== null && id !== undefined
      );
    }
  }),
};

export default createMigrate(migrations);

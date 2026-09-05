import { showError } from '~/features/snackbar/actions';
import {
  addtargetCNF,
  updateStatus1Sdal,
  updateStatus2Sdal,
  updateArmedStatus,
  updateHealth,
  updateChargingStatus,
  updateDETStatus,
} from '~/features/target/slice';

export const handleIncomeTargetCNF = (message, dispatch) => {
  dispatch(addtargetCNF(message));
};

export const handleIncomeSDALINF = (message, dispatch) => {
  // dispatch(showError(message.status1));
  console.log(message);
  dispatch(updateHealth(message.health));
  dispatch(updateStatus1Sdal(message.status1));
  dispatch(updateStatus2Sdal(message.status2));
  dispatch(updateArmedStatus(message.armed));
  dispatch(updateChargingStatus(message.charging));
  dispatch(updateDETStatus(message.DET));
};

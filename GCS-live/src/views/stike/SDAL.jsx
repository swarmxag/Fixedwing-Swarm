import React from 'react';
import {
  FormGroup,
  Button,
  Box,
  Paper,
  Typography,
  Chip,
  withStyles,
} from '@material-ui/core';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';
import CancelIcon from '@material-ui/icons/Cancel';
import messageHub from '~/message-hub';
import { MessageSemantics } from '~/features/snackbar/types';
import { showNotification } from '~/features/snackbar/slice';
import { connect } from 'react-redux';
import {
  getStatus1,
  getStatus2,
  getDETStatus,
  getArmedStatus,
  getHealthStatus,
  getChargingStatus,
} from '~/features/target/selectors';

const styles = (theme) => ({
  root: {
    margin: theme.spacing(2),
    padding: theme.spacing(3),
    // backgroundColor: theme.palette.background.paper,
    // borderRadius: theme.shape.borderRadius * 2,
    maxWidth: 700,
    maxHeight: 700,
    gap: 10,
    // boxShadow: theme.shadows[4],
  },
  statusRow: {
    display: 'flex',
    gap: theme.spacing(2),
    marginBottom: theme.spacing(2),
    alignItems: 'center',
  },
  chip: {
    minWidth: 120,
    fontWeight: 500,
    fontSize: 16,
    borderWidth: 2,
  },
  buttonGroup: {
    display: 'flex',
    flexDirection: 'row',
    gap: theme.spacing(2),
    marginTop: theme.spacing(1),
  },
});

const StatusChip = ({ label, status, classes, theme }) => (
  <Chip
    icon={
      status ? (
        <CheckCircleIcon style={{ color: theme.palette.success.main }} />
      ) : (
        <CancelIcon style={{ color: theme.palette.error.main }} />
      )
    }
    label={`${label}: ${status ? 'True' : 'False'}`}
    className={classes.chip}
    style={{
      borderColor: status
        ? theme.palette.success.main
        : theme.palette.error.main,
      color: status ? theme.palette.success.main : theme.palette.error.main,
      // background: status
      //   ? theme.palette.success.light
      //   : theme.palette.error.light,
    }}
    variant='outlined'
  />
);

const SDAL = ({
  status1,
  status2,
  dispatch,
  health,
  armed,
  classes,
  theme,
  charging,
  detStatus,
}) => {
  let initiall = true;
  const handleSubmit = async (msg) => {
    try {
      const res = await messageHub.sendMessage({
        type: 'X-SDAL',
        message: msg,
      });
      dispatch(
        showNotification({
          message: `${msg} sent ${res.body.result} Succesfully`,
          semantics: MessageSemantics.SUCCESS,
        })
      );
    } catch (error) {
      // dispatch(
      //   showNotification({
      //     message: `${msg} Failed`,
      //     semantics: MessageSemantics.ERROR,
      //   })
      // );
      console.log('e', error);
    }
  };

  // console.log(status1, status2, health, armed);

  return (
    <Box className={classes.root} elevation={4}>
      <Box className={classes.statusRow}>
        <StatusChip
          label='Health'
          status={health}
          classes={classes}
          theme={theme}
        />
        <StatusChip
          label='Armed'
          status={armed}
          classes={classes}
          theme={theme}
        />
        <StatusChip
          label='DET'
          status={detStatus}
          classes={classes}
          theme={theme}
        />
        <StatusChip
          label='Charged'
          status={!charging}
          classes={classes}
          theme={theme}
        />
      </Box>
      <FormGroup className={classes.buttonGroup}>
        <Button
          onClick={() => {
            handleSubmit('PWON');
            initiall = false;
          }}
          variant='contained'
          color='primary'
        >
          Power On
        </Button>
        <Button
          onClick={() => handleSubmit('PWOF')}
          variant='contained'
          color='primary'
        >
          Power Off
        </Button>
        <Button
          onClick={() => handleSubmit('ARM')}
          variant='contained'
          color='primary'
        >
          ARM
        </Button>
        <Button
          onClick={() => handleSubmit('DET')}
          variant='contained'
          style={{
            backgroundColor: theme.palette.warning.main,
            color: theme.palette.getContrastText(theme.palette.warning.main),
          }}
        >
          DET
        </Button>
        <Button
          onClick={() => handleSubmit('ABORT')}
          variant='contained'
          color='secondary'
        >
          ABORT
        </Button>
      </FormGroup>
      <Typography>
        {/* {!initiall && (charging ? 'Charging...' : 'charged')} */}
        {charging ? 'Charging...' : 'charged'}
      </Typography>
    </Box>
  );
};

export default connect(
  (state) => ({
    status1: getStatus1(state),
    status2: getStatus2(state),
    armed: getArmedStatus(state),
    detStatus: getDETStatus(state),
    health: getHealthStatus(state),
    charging: getChargingStatus(state),
  }),
  (dispatch) => ({
    dispatch,
  })
)(withStyles(styles, { withTheme: true })(SDAL));

{
  /*
drone number --> done
heading,height
target lat,lon
with RTL,without RTL
Strike
Abort mission
*/
}

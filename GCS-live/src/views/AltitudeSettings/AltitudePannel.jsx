import React from 'react';
import {Box, Button, FormControl, Input, InputLabel} from '@material-ui/core';
import {connect} from 'react-redux';
import {getUAVIdList} from "~/features/uavs/selectors";
import PropTypes from "prop-types";
import {makeStyles} from '@material-ui/core/styles';
import FormGroup from "@material-ui/core/FormGroup";
import messageHub from "~/message-hub";
import {showNotification} from "~/features/snackbar/slice";
import {MessageSemantics} from "~/features/snackbar/types";
import {showError} from "~/features/snackbar/actions";
import {changeAltitude, changeDifference,changeAltitudesArray,changeSingeAltitude,changeInitial,changeData,changeInitialDataTonule} from "~/features/altitudeSettings/slice";

const useStyles = makeStyles((theme) => ({
  wrapper: {
    display: 'flex',
    gap: theme.spacing(2),
    alignItems: 'center',
  },
  textId: {
    fontSize: 20,
  }
}))

const AltitudeSettings = ({ids, isHaveUavs, dispatch, altitudeSettings}) => {

  const classes = useStyles();

  React.useEffect(() => {
    if(!altitudeSettings.initial) return
    if (!isHaveUavs) return
    const newAltitudes = Array.from({length: ids.length}, (_, i) => altitudeSettings.altitude + i * altitudeSettings.difference);
    dispatch(changeAltitudesArray({altitudes:newAltitudes}));
    dispatch(changeInitial())
  }, [ids])

  const handleSendAltChange = async(sysid,alt) => {
    try {
      const res = await messageHub.sendMessage({
        type: 'X-SETTINGS',
        message: "different",
        // alt: alt,
        // id:sysid
        alt:altitudeSettings.altitude,
        alt_diff:altitudeSettings.difference,
      })
      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `Altitude is Successfully Changed`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      }
    } catch (e) {
      dispatch(showError(e?.message ? e.message : `Something went wrong in Changing Altitude of ${sysid}`));
    }
  }

  const calculateAltitudes = async () => {
    // dispatch(changeInitialDataTonule())
    const newAltitudes = Array.from({length: ids.length}, (_, i) => altitudeSettings.altitude + i * altitudeSettings.difference);
    dispatch(changeAltitudesArray({altitudes:newAltitudes}));

    for (let i in ids) {
      dispatch(changeData({index:ids[i],value:newAltitudes[i]}))
    }

    try {
      const res = await messageHub.sendMessage({
        // alts: altitudeSettings.data,
        type: 'X-UAV-socket',
        message: "different",
        // alt: alt,
        // id:sysid
        ids:ids,
        alt:altitudeSettings.altitude,
        alt_diff:altitudeSettings.difference,
      })
      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `Altitude is Successfully Changed`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      }
    } catch (error) {
      dispatch(showError('Something went wrong while trying to send altitudes.'));
    }

  };

  return (
    <Box style={{margin: 10, gap: 20, height: '100%'}}>
      <FormGroup style={{display: 'flex', flexDirection: 'row', gap: 15,alignItems:"center"}}>
        <FormControl variant='standard'>
          <InputLabel htmlFor='numofdrone'>Initial Height</InputLabel>
          <Input
            fullWidth={false}
            type='number'
            inputMode='numeric'
            name='altitude'
            inputProps={{id: 'altitude'}}
            value={altitudeSettings.altitude}
            onChange={({target: {value}}) => dispatch(changeAltitude({altitude:parseInt(value)}))}
          />
        </FormControl>
        <FormControl variant='standard'>
          <InputLabel htmlFor='numofdrone'>Height Difference</InputLabel>
          <Input
            fullWidth={false}
            type='number'
            inputMode='numeric'
            name='difference'
            inputProps={{id: 'difference'}}
            value={altitudeSettings.difference}
            onChange={({target: {value}}) => dispatch(changeDifference({difference:parseInt(value)}))}
          />
        </FormControl>
        <Button variant={'contained'} onClick={calculateAltitudes}>Save</Button>
      </FormGroup>
      {isHaveUavs && ids.map((id, i) => (
        <div key={id} className={classes.wrapper}>
          <p className={classes.textId}>Model: {parseInt(id)}</p>
          <Input
            fullWidth={false}
            type='number'
            inputMode='numeric'
            name={`altitude-${id}`}
            value={altitudeSettings.altitudes[i]}
            onChange={({target: {value}}) => dispatch(changeSingeAltitude({index:i, value:parseInt(value)}))}
          />
          <Button variant='contained' onClick={async () => handleSendAltChange(id,altitudeSettings.altitudes[i])}>Change Altitude</Button>
        </div>
      ))}
    </Box>
  );
};

AltitudeSettings.PropTypes = {
  ids: PropTypes.arrayOf(PropTypes.string).isRequired,
  isHaveUavs: PropTypes.bool.isRequired,
  altitudeSettings: PropTypes.shape({
    altitude: PropTypes.number,
    difference: PropTypes.number,
    data:PropTypes.object,
    initial:PropTypes.bool,
    altitudes:PropTypes.array
  })
}

export default connect(
  (state) => ({
    ids: getUAVIdList(state),
    isHaveUavs: getUAVIdList(state).length > 0,
    altitudeSettings: {
      ...state.altitudeSettings,
    }
  }),
  (dispatch) => ({
    dispatch,
  })
)(AltitudeSettings);

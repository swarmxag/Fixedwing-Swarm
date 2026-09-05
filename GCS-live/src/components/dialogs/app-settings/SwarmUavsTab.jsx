import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';

import Box from '@material-ui/core/Box';
import FormGroup from '@material-ui/core/FormGroup';
import Button from '@material-ui/core/Button';

import FormControl from "@material-ui/core/FormControl";
import InputLabel from "@material-ui/core/InputLabel";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Checkbox from "@material-ui/core/Checkbox";
import {SimpleAirspeedField} from '~/components/forms'
import messageHub from "~/message-hub";
import {showNotification} from "~/features/snackbar/slice";
import {MessageSemantics} from "~/features/snackbar/types";
import {changeRadius, changeDirection, changeSpeed} from "~/features/swarm/slice";
import {getRadius,getDirection,getSpeed} from "~/features/swarm/selectors";
import { getUAVIdList} from "~/features/uavs/selectors";
import {closeAppSettingsDialog} from "~/features/settings/actions";

const SwarmUavsTab = ({dispatch,speed,radius,direction,selectedIds,onClose}) => {

  const OnSubmit = async (msg) => {
    try {
      const res = await messageHub.sendMessage({
        type: 'X-SETTINGS',
        selected:selectedIds,
        message: msg,
        speed: speed,
        direction: direction,
        radius: radius,
      });

      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `${msg} is Successfully Changed`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
        onClose()
      }
    } catch (e) {
      dispatch(
        showNotification({
          message: `${e} Command is Failed`,
          semantics: MessageSemantics.ERROR,
        })
      );
      onClose()
    }
  }

  const handleSettings = async (msg) => {}

  return (
    <FormGroup style={{marginBottom: 3}}>
      <FormControl style={{alignItems: 'center', flexDirection: 'row',gap:10}}>
        <FormControlLabel
          label={'Speed of the Drones at Swarm'}
          control={<Checkbox checked style={{visibility: 'hidden'}}/>}
        />
        <SimpleAirspeedField
          name='airspeedThreshold'
          min={18}
          max={22}
          value={speed}
          variant='standard'
          onChange={(event) => dispatch(changeSpeed({speed: parseInt(event.target.value)}))}
        />
        <Button variant="contained" onClick={() => OnSubmit('speed')}>Change Speed</Button>
      </FormControl>
      <Box p={0.5}/>
      <FormControl style={{alignItems: 'center', flexDirection: 'row'}}>
        <FormControlLabel
          label={'Loiter Radius of Drones at Swarm'}
          control={<Checkbox checked style={{visibility: 'hidden'}}/>}
        />
        <SimpleAirspeedField
          name='radius'
          min={200}
          max={400}
          value={radius}
          variant='standard'
          onChange={(event) => dispatch(changeRadius({radius: parseInt(event.target.value)}))}
        />
      </FormControl>
      <Box mb={0.5}/>

      <Box display='flex' flexDirection='row' mb={1}>
        <FormControl fullWidth variant='filled'>
          <InputLabel id='direction-of-loiter'>
            Direction of Loiter
          </InputLabel>
          <Select
            labelId='direction-of-loiter'
            name='directionofloiter'
            value={direction}
            onChange={(event) => dispatch(changeDirection({direction: `${event.target.value}`}))}
          >
            <MenuItem value={'ClockWise Direction'}>
              ClockWise Direction
            </MenuItem>
            <MenuItem value={'Anti ClockWise Direction'}>
              Anti ClockWise Direction
            </MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Box mb={0.5}/>
      <Button variant="contained" onClick={async () => await OnSubmit('rad')}>Save</Button>
    </FormGroup>
  )
};

SwarmUavsTab.propTypes = {
  speed: PropTypes.number,
  direction: PropTypes.string,
  radius: PropTypes.number,
  selectedIds: PropTypes.array,
  onClose:PropTypes.func
};

export default connect(
  (state) => ({
    speed: getSpeed(state),
    direction: getDirection(state),
    radius: getRadius(state),
    selectedIds:getUAVIdList(state)
  }),
  (dispatch) => ({
    dispatch,
    onClose() {
      dispatch(closeAppSettingsDialog());
    },
  })
)(SwarmUavsTab);

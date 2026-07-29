import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  Box,
  FormGroup,
  FormControl,
  InputLabel,
  Input,
} from '@material-ui/core';
import { getCurrentServerState } from '~/features/servers/selectors';
import { showNotification } from '~/features/snackbar/slice';
import { MessageSemantics } from '~/features/snackbar/types';
import { connect } from 'react-redux';
import { withTranslation } from 'react-i18next';
import messageHub from '~/message-hub';
import {
  getSelectedFeatureIds,
  getFeatureById,
  getFeaturesInOrder,
} from '~/features/map-features/selectors';
import { getSelectedUAVIds } from '~/features/uavs/selectors';
import {
  changeCoverage,
  changeGridSpacing,
  openGroupSplitDialog,
  setTime,
  mergeMissionForUavs,
} from '~/features/swarm/slice';
import { showError } from '~/features/snackbar/actions';
import { getLandingMissionId } from '~/features/mission/selectors';
import {
  DownloadMissionTrue,
  setMissionFromServer,
} from '~/features/uavs/details';
import { ConnectionState } from '~/model/enums';

// const SwarmPanel = ({
//   selectedUAVIds,
//   selectedFeatureIds,
//   getFeatureBySelected,
//   dispatch,
//   socketData,
//   landingFeature,
//   features,
//   connection,
//   onOpen,
// }) => {
//   const handleLandingMission = async () => {
//     const landingMission = landingFeature();
//     let msg = 'Landing Misson and Command';
//     try {
//       const res = await messageHub.sendMessage({
//         type: 'X-UAV-socket',
//         message: 'landingMission',
//         landing: landingMission,
//         ids: selectedUAVIds,
//       });

//       if (Boolean(res?.body?.message)) {
//         dispatch(
//           showNotification({
//             message: `${msg} Message sent`,
//             semantics: MessageSemantics.SUCCESS,
//           })
//         );
//       }
//     } catch (e) {
//       dispatch(
//         showNotification({
//           message: `${msg} ${e?.message}`,
//           semantics: MessageSemantics.ERROR,
//         })
//       );
//     }
//   };

const SwarmPanel = ({
  selectedUAVIds,
  selectedFeatureIds,
  getFeatureBySelected,
  dispatch,
  socketData,
  antennaBearing,
  landingFeature,
  features,
  connection,
  onOpen,
}) => {
  useEffect(() => {
    if (connection !== ConnectionState.CONNECTED) {
      return;
    }

    (async () => {
      try {
        const res = await messageHub.sendMessage({
          type: 'X-UAV-socket',
          message: 'check_origin',
        });
        if (res?.body?.message === 'origin_not_set') {
          dispatch(showError('Origin/Geofence not set on the server — draw a geofence before sending commands'));
        }
      } catch (e) {
        // Best-effort startup check; a failure here shouldn't block the panel.
      }
    })();
  }, [connection]);

  const handleFenceMission = async () => {
    const featuresInMap = selectedFeatureIds.map((i) => {
      return getFeatureBySelected(i);
    });

    if (featuresInMap.length == 0) {
      showError('Select the Polygon or a Point in the Map');
      return;
    }
    // const validateFence = featuresInMap.filter((item) => item.label == 'outer' && item.type == 'polygon' && item.points.length == 4);
    // if(validateFence.length == 0){
    //   dispatch(showError('Fence name must be "outer" Only 4-point polygons are supported'));
    //   return;
    // }
    const validateFence = featuresInMap.filter(
      (item) =>
        item.label == 'outer' &&
        item.type == 'polygon' &&
        item.points.length >= 3  // ← any valid polygon needs at least 3 points
    );

    if (validateFence.length == 0) {
      dispatch(showError('Fence name must be "outer". Minimum 3-point polygon required.'));
      return;
    }


    try {
      const res = await messageHub.sendMessage({
        type: 'X-UAV-socket',
        message: 'fence',
        ids: selectedUAVIds,
        features: featuresInMap,
        ...socketData,
      });
      console.log('RES>>>>>>>>>>', res);

      if (res?.body?.message === 'in_obstacle') {
        dispatch(
          showNotification({
            message: 'UAV is inside an obstacle zone — geofence command ignored',
            semantics: MessageSemantics.WARNING,
          })
        );
        return;
      }
      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `Fence Mission Message sent`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      }
      if (res?.body?.message[0]?.length == 0) {
        dispatch(
          showNotification({
            message: `Read a Empty Mission`,
            semantics: MessageSemantics.WARNING,
          })
        );
        return;
      }
      console.log('Fence Mission Message Data', res.body.message);
      dispatch(setMissionFromServer(res.body.message));
      dispatch(
        showNotification({
          message: `${res.body.message[0].length}`,
          semantics: MessageSemantics.WARNING,
        })
      );
    } catch (e) {
      console.log(e);
      dispatch(showError(`Fence Mission Message failed to send`));
    }
  };


  const handleSplitMission = async () => {
    const selectedFeatures = selectedFeatureIds.map((i) => getFeatureBySelected(i));
    const coords = selectedFeatures.filter((item) => item.type === 'points');
    const points = coords.map((coord) => coord.points[0]);
    if (coords.length === 0) {
      showError('There is No Point in the map for Searching Area');
      return;
    }
    try {
      const res = await messageHub.sendMessage({
        type: 'X-UAV-socket',
        message: 'groupsplit',
        coords: points,
        ids: selectedUAVIds,
        ...socketData,
      });
      const splitErrorMessages = {
        no_fence_drawn: 'Draw a geofence (Set Origin) before splitting the group',
        uav_selection_mismatch: "Selected UAVs don't match connected UAVs",
        error: 'Split Mission failed on the server',
      };
      if (splitErrorMessages[res?.body?.message]) {
        dispatch(showError(splitErrorMessages[res.body.message]));
        return;
      }
      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `split Mission Message sent`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      }
      if (res?.body?.message[0]?.length == 0) {
        dispatch(
          showNotification({
            message: `Read a Empty Mission`,
            semantics: MessageSemantics.WARNING,
          })
        );
        return;
      }
      dispatch(setMissionFromServer(res.body.message));
      if (res?.body?.missionByUav) {
        dispatch(mergeMissionForUavs(res.body.missionByUav));
      }
      dispatch(
        showNotification({
          message: `${res.body.message[0].length}`,
          semantics: MessageSemantics.WARNING,
        })
      );
    } catch (e) {
      dispatch(showError(`Split Mission Message failed to send`));
    }
  };

  const handleMsg = async (msg) => {
    try {
      const res = await messageHub.sendMessage({
        type: 'X-UAV-socket',
        message: msg,
        id: selectedUAVIds[0],
      });
      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `${msg} Message sent`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      }
    } catch (e) {
      dispatch(showError(`${msg} Message failed to send`));
    }
  };

  const handlePoint = async (message) => {
    if (selectedFeatureIds.length === 0) {
      dispatch(showError(`${message} needs a path or point`));
      return;
    }
    const featureId = selectedFeatureIds[0];
    const data = getFeatureBySelected(featureId);
    try {
      const res = await messageHub.sendMessage({
        type: 'X-UAV-socket',
        message,
        ids: selectedUAVIds,
        coords: data.points,
        ...socketData,
      });

      if (res?.body?.message === 'origin_not_set') {
        dispatch(showError('Draw a geofence (Set Origin) before sending this command'));
        return;
      }

      if (Boolean(res.body.message)) {
        dispatch(
          showNotification({
            message: `${message} Message sent`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      } else {
        dispatch(showError(`${message} failed to send`));
      }

      if (message == 'search' || message == 'navigate') {
        if (res?.body?.message[0]?.length == 0) {
          dispatch(
            showNotification({
              message: `Read a Empty Mission`,
              semantics: MessageSemantics.WARNING,
            })
          );
          return;
        }
        dispatch(setMissionFromServer(res.body.message));
        dispatch(setTime(res.body.time?.toFixed(2)));
        if (res?.body?.missionByUav) {
          dispatch(mergeMissionForUavs(res.body.missionByUav));
        }
      }
    } catch (e) {
      dispatch(
        showNotification({
          message: `${message} ${e?.message} Command is Failed`,
          semantics: MessageSemantics.ERROR,
        })
      );
    }
  };

  return (
    <Box style={{ margin: 10, gap: 20 }}>
      <FormGroup style={{ display: 'flex', flexDirection: 'row', gap: 15 }}>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          {/*<FormControl fullWidth variant='standard'>*/}
          {/*  <Button*/}
          {/*    variant='contained'*/}
          {/*    onClick={async () => await handleMsg('master')}*/}
          {/*    disabled={selectedUAVIds?.length !== 1}*/}
          {/*  >*/}
          {/*    Master*/}
          {/*  </Button>*/}
          {/*</FormControl>*/}
          {/*<FormControl fullWidth variant='standard'>*/}
          {/*  <label onClick={() => setEditing(true)}>*/}
          {/*    <ListItem button>*/}
          {/*      Choose Runway: {val.location} {val.runwayName}*/}
          {/*    </ListItem>*/}
          {/*  </label>*/}
          {/*  <DraggableDialog*/}
          {/*    fullWidth*/}
          {/*    open={editing}*/}
          {/*    maxWidth='sm'*/}
          {/*    title='Choose Runway'*/}
          {/*    onClose={() => {*/}
          {/*      setVal((prev) => {*/}
          {/*        return {*/}
          {/*          ...prev,*/}
          {/*          location: '',*/}
          {/*          runwayName: '',*/}
          {/*        };*/}
          {/*      });*/}
          {/*      setEditing(false);*/}
          {/*    }}*/}
          {/*  >*/}
          {/*    <DialogContent>*/}
          {/*      <FormGroup>*/}
          {/*        <FormControl fullWidth variant='standard'>*/}
          {/*          <InputLabel id='location'>Location:</InputLabel>*/}
          {/*          <Select*/}
          {/*            fullWidth*/}
          {/*            value={val.location}*/}
          {/*            onChange={({ target: { value } }) => {*/}
          {/*              setVal((prev) => {*/}
          {/*                return {*/}
          {/*                  ...prev,*/}
          {/*                  location: value,*/}
          {/*                };*/}
          {/*              });*/}
          {/*            }}*/}
          {/*          >*/}
          {/*            {swarm_location.map((loc) => (*/}
          {/*              <MenuItem value={loc}>{loc}</MenuItem>*/}
          {/*            ))}*/}
          {/*          </Select>*/}
          {/*        </FormControl>*/}
          {/*        <FormControl*/}
          {/*          fullWidth*/}
          {/*          variant='filled'*/}
          {/*          style={{ marginTop: 5 }}*/}
          {/*        >*/}
          {/*          <FormLabel id='runway' style={{ marginTop: 20 }}>*/}
          {/*            Select position*/}
          {/*          </FormLabel>*/}
          {/*          <RadioGroup aria-labelledby='runway' row>*/}
          {/*            {runway?.length != 0 &&*/}
          {/*              runway.map((item) => (*/}
          {/*                <FormControlLabel*/}
          {/*                  label={item}*/}
          {/*                  value={item}*/}
          {/*                  control={<Radio checked={val.runwayName == item} />}*/}
          {/*                  onChange={() => {*/}
          {/*                    setVal((prev) => {*/}
          {/*                      return {*/}
          {/*                        ...prev,*/}
          {/*                        runwayName: item,*/}
          {/*                      };*/}
          {/*                    });*/}
          {/*                  }}*/}
          {/*                />*/}
          {/*              ))}*/}
          {/*          </RadioGroup>*/}
          {/*        </FormControl>*/}
          {/*        <Button*/}
          {/*          variant='contained'*/}
          {/*          disabled={!(val.location != '' && val.runwayName != '')}*/}
          {/*          onClick={() => {*/}
          {/*            setEditing(false);*/}
          {/*            handleMsg('plot');*/}
          {/*          }}*/}
          {/*        >*/}
          {/*          Submit*/}
          {/*        </Button>*/}
          {/*      </FormGroup>*/}
          {/*    </DialogContent>*/}
          {/*  </DraggableDialog>*/}
          {/*</FormControl>*/}
        </Box>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <FormControl
            fullWidth
            variant='standard'
            style={{ display: 'flex', flexDirection: 'row', gap: 10 }}
          >
            <Button
              variant='contained'
              onClick={async () => await handlePoint('navigate')}
            >
              Navigation
            </Button>
            {/*<Button variant='contained' onClick={async () => await handleMsg('clear_csv')}>*/}
            {/*  Clear CSV*/}
            {/*</Button>*/}
            {/* <Button variant='contained' onClick={}>
              Home
            </Button> */}
          </FormControl>
        </Box>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <FormControl
            fullWidth
            variant='standard'
            style={{ display: 'flex', flexDirection: 'row', gap: 10 }}
          >
            {/*<Button variant='contained' onClick={async () => await handlePoint('loiter')}>*/}
            {/*  Loiter Point*/}
            {/*</Button>*/}
            <Button
              variant='contained'
              onClick={async () => await handlePoint('goal')}
            >
              Goal Point
            </Button>
            <Button
              variant='contained'
              onClick={handleFenceMission}
            >
              Set Origin
            </Button>
          </FormControl>
        </Box>
        <Box
          style={{
            display: 'flex',
            gap: 20,
            alignItems: 'center',
          }}
        >
          <FormControl
            fullWidth
            variant='standard'
            style={{
              display: 'flex',
              flexDirection: 'row',
              gap: 10,
              alignItems: 'center',
            }}
          >
            {/*<Button variant='contained' onClick={async () => await handleMsg('share_data')}>*/}
            {/*  share data*/}
            {/*</Button>*/}
            {/*<Button variant='contained' onClick={async () => await handleMsg('home_lock')}>*/}
            {/*  Home Lock*/}
            {/*</Button>*/}
            <Button
              variant='contained'
              onClick={async () => await handleMsg('add_link')}
            >
              Add Link
            </Button>
            <Button
              variant='contained'
              onClick={async () => await handleMsg('remove_link')}
            >
              Remove Link
            </Button>
            <Button
              variant='contained'
              onClick={() => dispatch(onOpen())}
              // disabled={selectedUAVIds.length === 0}
            >
              Open Group
            </Button>
            {/* Estimated time: {socketData.time} minutes */}
          </FormControl>
        </Box>
        <Box
          style={{
            display: 'flex',
            gap: 20,
            alignItems: 'center',
          }}
        >
          {/*<FormControl*/}
          {/*  variant='standard'*/}
          {/*  style={{display: 'flex', flexDirection: 'row', gap: 10}}*/}
          {/*>*/}
          {/*  <InputLabel id='goal'>Skip Waypoit</InputLabel>*/}
          {/*  <Input*/}
          {/*    id='goal'*/}
          {/*    value={socketData.skip_waypoint}*/}
          {/*    type='number'*/}
          {/*    onChange={({target: {value}}) => dispatch(changeWayPoint({waypoint:parseInt(value)}))}*/}
          {/*  />*/}
          {/*</FormControl>*/}
          {/*<Button*/}
          {/*  variant='contained'*/}
          {/*  onClick={async () => await handlePoint('skip')}*/}
          {/*>*/}
          {/*  Skip*/}
          {/*</Button>*/}
          {/*<FormControl*/}
          {/*  variant='standard'*/}
          {/*  style={{display: 'flex', flexDirection: 'row', gap: 10}}*/}
          {/*>*/}
          {/*  <InputLabel id='alt'>Alt</InputLabel>*/}
          {/*  <Input*/}
          {/*    id='alt'*/}
          {/*    value={val.alt}*/}
          {/*    type='number'*/}
          {/*    onChange={({target: {value}}) => {*/}
          {/*      setVal((prev) => {*/}
          {/*        return {...prev, alt: parseInt(value)};*/}
          {/*      });*/}
          {/*    }}*/}
          {/*  />*/}
          {/*</FormControl>*/}
          {/*<FormControl>*/}
          {/*  <InputLabel id='alt_diff'>Different Alt</InputLabel>*/}
          {/*  <Input*/}
          {/*    id='alt_diff'*/}
          {/*    value={val.alt_diff}*/}
          {/*    type='number'*/}
          {/*    onChange={({target: {value}}) => {*/}
          {/*      setVal((prev) => {*/}
          {/*        return {...prev, alt_diff: parseInt(value)};*/}
          {/*      });*/}
          {/*    }}*/}
          {/*  />*/}
          {/*</FormControl>*/}
          {/*<Button variant='contained' onClick={handleAlt} disabled={!val.alt}>*/}
          {/*  Set Alt*/}
          {/*</Button>*/}
          <FormControl variant='standard'>
            <InputLabel htmlFor='coverage'>Coverage in Meters</InputLabel>
            <Input
              name='coverage'
              type='number'
              inputMode='numeric'
              inputProps={{ id: 'coverage' }}
              value={socketData.coverage}
              onChange={({ target: { value, name } }) =>
                dispatch(changeCoverage({ coverage: parseInt(value) }))
              }
            />
          </FormControl>
          <FormControl variant='standard'>
            <InputLabel htmlFor='gridSpacing'>
              Grid Spacing in Meters
            </InputLabel>
            <Input
              name='gridSpacing'
              type='number'
              inputMode='numeric'
              inputProps={{ id: 'gridSpacing' }}
              value={socketData.gridSpacing}
              onChange={({ target: { value, name } }) =>
                dispatch(changeGridSpacing({ gridSpacing: parseInt(value) }))
              }
            />
          </FormControl>
          {/*<Button variant='contained' onClick={async () => await handleMsg('stop')}>*/}
          {/*  Stop*/}
          {/*</Button>*/}
          <Button
            variant='contained'
            onClick={async () => await handlePoint('search')}
          >
            Search
          </Button>
          <Button
            variant='contained'
            onClick={handleSplitMission}
            disabled={selectedUAVIds.length === 0}
          >
            Split Group
          </Button>
        </Box>
        <FormControl
          fullWidth
          style={{ display: 'flex', flexDirection: 'row', gap: 10 }}
        >
          {/*<Button variant='contained' onClick={async () => await handleMsg('remove_uav')}>*/}
          {/*  Remove Uav*/}
          {/*</Button>*/}
          {/*<Button variant='contained' onClick={async () => await handleMsg('payload')}>*/}
          {/*  Release Payload*/}
          {/*</Button>*/}
          <Button
            variant='contained'
            onClick={() => dispatch(DownloadMissionTrue())}
          >
            show Trajectory
          </Button>
        </FormControl>
      </FormGroup>
    </Box>
  );
};

SwarmPanel.propTypes = {
  selectedUAVIds: PropTypes.arrayOf(PropTypes.string),
  selectedFeatureIds: PropTypes.arrayOf(PropTypes.string),
  getFeatureBySelected: PropTypes.func,
  socketData: PropTypes.object,
  landingFeature: PropTypes.func,
};

export default connect(
  // mapStateToProps
  (state) => ({
    selectedUAVIds: getSelectedUAVIds(state),
    selectedFeatureIds: getSelectedFeatureIds(state),
    features: getFeaturesInOrder(state),
    getFeatureBySelected: (featureId) => getFeatureById(state, featureId),
    landingFeature: () => {
      const landingMissionId = getLandingMissionId(state);
      const landingFeature = getFeatureById(state, landingMissionId);
      if (landingFeature === undefined) return [];
      return landingFeature?.points;
    },
    socketData: {
      ...state.socket,
    },
    connection: getCurrentServerState(state).state,
  }),
  // mapDispatchToProps
  (dispatch) => ({
    dispatch,
    onOpen: openGroupSplitDialog,
  })
)(withTranslation()(SwarmPanel));

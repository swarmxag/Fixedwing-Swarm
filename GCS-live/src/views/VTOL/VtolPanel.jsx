import React, { useState, useEffect } from 'react';
import {
  Button,
  Box,
  FormControl,
  FormGroup,
  InputLabel,
  Input,
  RadioGroup,
  FormLabel,
  FormControlLabel,
  Radio,
  Select,
  Divider,
  MenuItem,
} from '@material-ui/core';
import {
  getFeaturesInOrder,
  getFeatureById,
} from '~/features/map-features/selectors';
import messageHub from '~/message-hub';
import { MessageSemantics } from '~/features/snackbar/types';
import { showNotification } from '~/features/snackbar/slice';
import { connect } from 'react-redux';
import {
  setMissionFromServer,
  DownloadMissionTrue,
} from '~/features/uavs/details';
import { getSelectedUAVIds } from '~/features/uavs/selectors';
import { setSelectedTool } from '~/features/map/tools';
import { getUAVIdList } from '~/features/uavs/selectors';
import {
  getInitialMissionId,
  getLandingMissionId,
} from '~/features/mission/selectors';
import { Tool } from '~/views/map/tools';
import { openOnLoadImage } from '~/features/show/slice';

const VtolPanel = ({
  selectedUAVIds,
  onToolSelected,
  features,
  dispatch,
  ids,
  initalFeature,
  onLoadImage,
  landingFeature,
}) => {
  const [data, setData] = useState({
    numofdrone: 0,
    turn: '',
    skip: 0,
    uavid: 0,
    missiontype: 'fixed type',
    coverage: 1000,
    gridspacing: 50,
    // type: 'target',
    lat: 0,
    lon: 0,
  });

  useEffect(() => {
    if (!selectedUAVIds?.length) return;
    setData((prev) => {
      return { ...prev, uavid: selectedUAVIds[0] };
    });
  }, [selectedUAVIds]);

  const handleMsg = async (msg) => {
    let body = {};
    const initialMission = initalFeature();
    const landingMission = landingFeature();
    const coords = features.filter((item) => item.type === 'points');
    if (msg == 'uploadmission') {
      if (data.numofdrone == 0 && data.turn == '') {
        dispatch(
          showNotification({
            message: `Failed to send message ${msg} due to invalid inputs`,
            semantics: MessageSemantics.ERROR,
          })
        );
        return;
      }
      if (data.missiontype == 'fixed type') {
        if (initialMission.length > 0 && landingMission.length > 0) {
          body = { mission: initialMission, landingMission: landingMission };
        } else {
          dispatch(
            showNotification({
              message: `Failed to send message ${msg} due to Initial or Landing Mission is Empty or Mission Type is not Fixed`,
              semantics: MessageSemantics.ERROR,
            })
          );
          return;
        }
      }
      if (coords.length > 0) {
        const coord = coords[0].points[0];
        body = { ...body, points: [...coord] };
      }
      if (data.numofdrone == 0) {
        dispatch(
          showNotification({
            message: `Failed to send message ${msg} due to Number of drones is ${data.numofdrone} equal to 'ZERO'`,
            semantics: MessageSemantics.ERROR,
          })
        );
        return;
      }
    }

    if (msg == 'spilt_mission') {
      const coord = coords.map((item) => item.points[0]);
      body = { center_latlon: coord };
    }
    try {
      const res = await messageHub.sendMessage({
        type: 'X-VTOL-MISSION',
        message: msg,
        ids,
        selected: selectedUAVIds,
        ...data,
        ...body,
      });

      if (Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `${msg} Message sent`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      }

      if (msg === 'download') {
        dispatch(
          showNotification({
            message: `${res?.body?.message[0]?.length} Download`,
            semantics: MessageSemantics.WARNING,
          })
        );
        if (res?.body?.message[0]?.length == 0) {
          dispatch(
            showNotification({
              message: `Read a Empty Mission`,
              semantics: MessageSemantics.ERROR,
            })
          );
          return;
        }
        dispatch(
          showNotification({
            message: `${msg} AFTER`,
            semantics: MessageSemantics.WARNING,
          })
        );
        dispatch(setMissionFromServer(res.body.message));
      }
    } catch (e) {
      dispatch(
        showNotification({
          message: `${msg} ${e?.message}`,
          semantics: MessageSemantics.ERROR,
        })
      );
    }
  };

  return (
    <Box style={{ margin: 10, gap: 20, height: '100%' }}>
      <FormGroup style={{ display: 'flex', flexDirection: 'row', gap: 15 }}>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <FormControl fullWidth variant='standard'>
            <InputLabel htmlFor='numofdrone'>Number of Drones</InputLabel>
            <Input
              type='number'
              inputMode='numeric'
              name='numofdrone'
              inputProps={{ id: 'numofdrone' }}
              value={data.numofdrone}
              onChange={({ target: { value, name } }) =>
                setData((prev) => {
                  return { ...prev, [name]: value };
                })
              }
            />
          </FormControl>
          <FormControl fullWidth variant='standard'>
            <FormLabel htmlFor='turn'>Choose Turn:</FormLabel>
            <RadioGroup
              row
              inputProps={{ id: 'turn' }}
              defaultValue=''
              name='turn'
              value={data.turn}
              onChange={({ target: { value, name } }) =>
                setData((prev) => {
                  return { ...prev, [name]: value };
                })
              }
            >
              <FormControlLabel
                value='right'
                control={<Radio checked={data.turn === 'right'} />}
                label='Right'
              />
              <FormControlLabel
                value='left'
                control={<Radio checked={data.turn === 'left'} />}
                label='Left'
              />
            </RadioGroup>
          </FormControl>
          <Select
            value={data.missiontype}
            onChange={({ target }) => {
              setData((prev) => {
                return { ...prev, missiontype: target.value };
              });
            }}
          >
            <MenuItem value={'fixed type'}>Fixed Type</MenuItem>
            <MenuItem value={'dynamic type'}>Dynamic Type</MenuItem>
          </Select>
          <FormControl fullWidth variant='standard'>
            <Button
              variant='contained'
              disabled={!(data.numofdrone && data.turn != '')}
              onClick={() => handleMsg('uploadmission')}
            >
              Upload Mission
            </Button>
          </FormControl>
          <FormControl fullWidth variant='standard'>
            <Button
              variant='contained'
              onClick={() => handleMsg('spilt_mission')}
            >
              Split Mission
            </Button>
          </FormControl>
        </Box>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <Button variant='contained' onClick={() => handleMsg('download')}>
            Download All Mission
          </Button>
          <Button
            variant='contained'
            onClick={() => dispatch(DownloadMissionTrue())}
          >
            Plot the Mission
          </Button>
        </Box>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <FormControl variant='standard'>
            <InputLabel htmlFor='skip'>Skip waypoint</InputLabel>
            <Input
              name='skip'
              type='number'
              inputMode='numeric'
              inputProps={{ id: 'skip' }}
              value={data.skip}
              onChange={({ target: { value, name } }) =>
                setData((prev) => {
                  return { ...prev, [name]: value };
                })
              }
            />
          </FormControl>
          <Button variant='contained' onClick={() => handleMsg('Skipwaypoint')}>
            Skip waypoint
          </Button>
        </Box>
      </FormGroup>
      <Divider style={{ margin: 10 }} />
      <Box
        style={{ display: 'flex', gap: 20, alignItems: 'center', margin: 10 }}
      >
        <Button
          onClick={() => {
            dispatch(onToolSelected(Tool.DRAW_POINT));
          }}
        >
          Add Target
        </Button>
        <FormControl variant='standard'>
          <InputLabel htmlFor='skip'>Coverage in Meters</InputLabel>
          <Input
            name='coverage'
            type='number'
            inputMode='numeric'
            inputProps={{ id: 'coverage' }}
            value={data.coverage}
            onChange={({ target: { value, name } }) =>
              setData((prev) => {
                return { ...prev, [name]: value };
              })
            }
          />
        </FormControl>
        <FormControl variant='standard'>
          <InputLabel htmlFor='skip'>Grid Spacing in Meters</InputLabel>
          <Input
            name='gridspacing'
            type='number'
            inputMode='numeric'
            inputProps={{ id: 'gridspacing' }}
            value={data.gridspacing}
            onChange={({ target: { value, name } }) =>
              setData((prev) => {
                return { ...prev, [name]: value };
              })
            }
          />
        </FormControl>
        <Button onClick={handleMsg.bind(this, 'grid')}>Submit</Button>
      </Box>
      {/* <Box style={{ display: 'flex', gap: 5 }}>
        <Button
          variant='contained'
          onClick={handleMsg.bind(this, 'start_capture')}
        >
          Start Capture
        </Button>
        <Button
          variant='contained'
          onClick={handleMsg.bind(this, 'stop_capture')}
        >
          Stop Capture
        </Button>
      </Box> */}
      <Box
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'center',
        }}
      >
        <FormControl variant='standard'>
          <InputLabel htmlFor='skip'>Latitude</InputLabel>
          <Input
            name='lat'
            type='number'
            inputMode='numeric'
            inputProps={{ id: 'lat' }}
            value={data.lat}
            onChange={({ target: { value, name } }) =>
              setData((prev) => {
                return { ...prev, [name]: value };
              })
            }
          />
        </FormControl>
        <FormControl variant='standard'>
          <InputLabel htmlFor='skip'>Longitude</InputLabel>
          <Input
            name='lon'
            type='number'
            inputMode='numeric'
            inputProps={{ id: 'lon' }}
            value={data.lon}
            onChange={({ target: { value, name } }) =>
              setData((prev) => {
                return { ...prev, [name]: value };
              })
            }
          />
        </FormControl>
        {/* <Select
          value={data.type}
          onChange={({ target }) => {
            setData((prev) => {
              return { ...prev, type: target.value };
            });
          }}
        >
          <MenuItem value={'payload'}>Payload Drop</MenuItem>
          <MenuItem value={'target'}>Target</MenuItem>
        </Select> */}
        <Button
          onClick={handleMsg.bind(this, 'target')}
          disabled={data.lat == 0 && data.lon == 0}
        >
          Set Target
        </Button>
      </Box>
      {/* <Button
        onClick={handleMsg.bind(this, 'target')}
        // disabled={data.lat == 0 && data.lon == 0}
      >
        Target
      </Button> */}
    </Box>
  );
};

export default connect(
  (state) => ({
    selectedUAVIds: getSelectedUAVIds(state),
    features: getFeaturesInOrder(state),
    ids: getUAVIdList(state),
    initalFeature: () => {
      const initialMissionId = getInitialMissionId(state);
      const feature = getFeatureById(state, initialMissionId);
      if (feature === undefined) return [];
      return feature?.points;
    },
    landingFeature: () => {
      const landingMissionId = getLandingMissionId(state);
      const landingFeature = getFeatureById(state, landingMissionId);
      if (landingFeature === undefined) return [];
      return landingFeature?.points;
    },
  }),
  (dispatch) => ({
    onToolSelected: setSelectedTool,
    dispatch,
    onLoadImage: openOnLoadImage,
  })
)(VtolPanel);

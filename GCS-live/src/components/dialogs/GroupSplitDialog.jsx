import * as React from 'react';
import {
  MenuItem,
  FormControl,
  Select,
  Button,
  DialogActions,
  DialogContent,
  DialogContentText,
  Box,
  Tab,
  Dialog,
  Chip,
  OutlinedInput,
  InputLabel,
  IconButton,
} from '@material-ui/core';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import {
  closeGroupSplitingDialog,
  addGroup,
  changeSelectedTab,
  resetGroup,
  setTime,
  mergeMissionForUavs,
} from '~/features/swarm/slice';
// import DronePlaceholderList from '~/components/uavs/DronePlaceholderList';
import { getUAVIdList } from '~/features/uavs/selectors';
import DialogTabs from '@skybrush/mui-components/lib/DialogTabs';
import {
  getFeatureByPoints,
  getGroup,
  getGroupByObject,
} from '~/features/swarm/selectors';
import { showError, showNotification } from '~/features/snackbar/actions';
import { MessageSemantics } from '~/features/snackbar/types';
import DeleteIcon from '@material-ui/icons/Delete';
import messageHub from '~/message-hub';
import { getFeatureById } from '~/features/map-features/selectors';

import store from '~/store';
import { setMissionFromServer } from '~/features/uavs/details';

const { getState } = store;

const MultipleSelectChip = ({
  onClose,
  open,
  uavIds,
  features,
  group,
  markerExists,
  SplitGroup,
  showErrorMsg,
  showMsg,
  onTabSelected,
  selectedTab,
  deleteAllGroup,
  gridSpacing,
  coverage,
  featurePoints,
  dispatch,
}) => {
  let content;
  const actions = [];

  const [inputs, setInputs] = React.useState([]);

  const addInput = () => {
    setInputs([...inputs, { id: Date.now(), value: '', uavs: [] }]); // Add an input object
  };

  const removeInput = () => {
    setInputs([]);
  };

  const updateInput = (id, newValue) => {
    setInputs(
      inputs.map((input) =>
        input.id === id ? { ...input, value: newValue } : input
      )
    );
  };

  const deleteInput = (id) => {
    setInputs(inputs.filter((input) => input.id !== id));
  };

  const valueExists = (listTocheck) =>
    listTocheck.some((value) =>
      Object.values(getState().socket.group).some((arr) => arr.includes(value))
    );

  const updateUav = (id, uavslist) => {
    setInputs(
      inputs.map((input) => {
        if (input.id === id) {
          return { ...input, uavs: uavslist };
        }
        return input;
      })
    );
  };

  const creategroup = () => {
    const nextGroup = {};
    for (const val in inputs) {
      if (!inputs[val].value) {
        showErrorMsg(`Select an area for every group`);
        return null;
      }
      if (inputs[val].uavs?.length == 0) {
        showErrorMsg(`There is No UAV Selected`);
        return null;
      }
      const value = featurePoints(inputs[val].value);
      const groupKey = String(value);
      const alreadyExist = Object.prototype.hasOwnProperty.call(nextGroup, groupKey);
      const uavExist = inputs[val].uavs.some((uav) =>
        Object.values(nextGroup).some((arr) => arr.includes(uav))
      );
      if (alreadyExist || uavExist) {
        showErrorMsg(
          `${inputs[val].value} is already in a Group or uav is already exist in one of the group`
        );
        return null;
      }
      nextGroup[groupKey] = inputs[val].uavs;
      SplitGroup({ id: value, uavs: inputs[val].uavs });
      showMsg(`${inputs[val].value} is added to a Group`);
    }
    return nextGroup;
  };

  const handleSubmit = async () => {
    deleteAllGroup();
    const nextGroup = creategroup();
    if (!nextGroup) {
      return;
    }
    try {
      const res = await messageHub.sendMessage({
        type: 'X-UAV-socket',
        message: 'spificsplit',
        groups: nextGroup,
        coverage: coverage,
        gridSpacing: gridSpacing,
      });
      const splitErrorMessages = {
        no_fence_drawn: 'Draw a geofence (Set Origin) before splitting the group',
        uav_coverage_mismatch:
          "Group assignment isn't valid: a UAV must be connected, unassigned elsewhere, and assigned to at most one group",
        error: 'Split Mission failed on the server',
      };
      if (splitErrorMessages[res?.body?.message]) {
        showErrorMsg(splitErrorMessages[res.body.message]);
        return;
      }
      if (Boolean(res?.body?.message)) {
        showMsg('split Mission Message sent');
      }
      if (res?.body?.message[0]?.length == 0) {
        showMsg('Read a Empty Mission');
        return;
      }
      showMsg(typeof res.body.time?.toFixed(2));
      dispatch(setMissionFromServer(res.body.message));
      if (res?.body?.missionByUav) {
        dispatch(mergeMissionForUavs(res.body.missionByUav));
      }
      dispatch(setTime(res.body.time?.toFixed(2)));
    } catch (err) {
      showErrorMsg(err?.message);
    }
  };

  if (features?.length == 0) {
    content = (
      <DialogContent>
        <p>Feature does not exist</p>
      </DialogContent>
    );
  } else {
    switch (selectedTab) {
      case 'Create':
        content = (
          <DialogContent>
            <Button onClick={addInput}>Add Group</Button>
            {inputs.map((input, i) => (
              <Box
                style={{
                  marginTop: 5,
                  marginBottom: 5,
                  display: 'flex',
                  flexDirection: 'row',
                  gap: 20,
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <FormControl fullWidth>
                  <InputLabel id='demo-multiple-chip-label'>
                    Group {i + 1}
                  </InputLabel>
                  <Select
                    labelId='demo-multiple-chip-label'
                    style={{ flex: 1 }}
                    type='text'
                    value={input.value}
                    onChange={(e) => updateInput(input.id, e.target.value)}
                    className='w-full p-2 border rounded-lg'
                    placeholder={`Input ${input.id}`}
                  >
                    {features.map((val) => (
                      <MenuItem value={val.id}>{val.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <Select
                    id='demo-multiple-chip'
                    multiple
                    style={{ flex: 1 }}
                    value={input.uavs}
                    onChange={(e) => updateUav(input.id, e.target.value)}
                    // input={
                    //   <OutlinedInput id='select-multiple-chip' label='Chip' />
                    // }
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    {uavIds.map((name) => (
                      <MenuItem key={name} value={name}>
                        {name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <IconButton
                  aria-label='delete'
                  onClick={() => deleteInput(input.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            ))}
          </DialogContent>
        );
        actions.push(
          <Button onClick={handleSubmit}>Submit</Button>,
          <Button onClick={onClose}>Close</Button>,
          <Button
            onClick={() => {
              removeInput();
              deleteAllGroup();
            }}
          >
            Reset Group
          </Button>
        );
        break;

      case 'Delete':
        content = <DialogContent>Delete</DialogContent>;
        break;

      default:
        content = <DialogContent>Default</DialogContent>;
    }
  }

  return (
    <Dialog
      fullWidth
      open={open}
      maxWidth='sm'
      title='Group Spliting'
      onClose={onClose}
    >
      <DialogTabs value={selectedTab} onChange={onTabSelected}>
        <Tab value='Create' label='Create Group' />
        <Tab value='Delete' label='Delete Group' />
      </DialogTabs>

      {content}
      <DialogActions>
        {actions}
        {/* <Button onClick={handleSubmit}>Submit</Button>
        <Button onClick={onClose}>Close</Button> */}
      </DialogActions>
    </Dialog>
  );
};

MultipleSelectChip.propTypes = {
  onClose: PropTypes.func,
  open: PropTypes.bool,
  uavIds: PropTypes.arrayOf(PropTypes.string),
  features: PropTypes.arrayOf(PropTypes.object).isRequired,
  group: PropTypes.object,
  markerExists: PropTypes.func,
  SplitGroup: PropTypes.func,
  showErrorMsg: PropTypes.func,
  showMsg: PropTypes.func,
  selectedTab: 'Create' | 'Delete' | 'View Groups',
  onTabSelected: PropTypes.func,
  deleteAllGroup: PropTypes.func,
  coverage: PropTypes.number,
  gridSpacing: PropTypes.number,
  featurePoints: PropTypes.func,
};

const GroupSplitDialog = connect(
  // mapStateToProps
  (state) => ({
    open: state.socket.groupsplitDialog,
    uavIds: getUAVIdList(state),
    features: getFeatureByPoints(state),
    group: getGroup(state),
    markerExists: (markerToCheck) => {
      return getState().socket.group.hasOwnProperty(markerToCheck);
    },
    selectedTab: state.socket.selectedTab,
    coverage: state.socket.coverage,
    gridSpacing: state.socket.gridSpacing,
    featurePoints: (featureId) => {
      const feature = getFeatureById(state, featureId);
      return [feature.points[0][1], feature.points[0][0]];
    },
  }),
  // mapDispatchToProps
  (dispatch) => ({
    onClose: () => dispatch(closeGroupSplitingDialog()),
    SplitGroup: ({ id, uavs }) => dispatch(addGroup({ id, uavs })),
    showErrorMsg: (msg) => dispatch(showError(msg)),
    showMsg: (msg) =>
      dispatch(
        showNotification({
          message: msg,
          semantics: MessageSemantics.INFO,
        })
      ),
    onTabSelected(_event, value) {
      dispatch(changeSelectedTab(value));
    },
    deleteAllGroup() {
      dispatch(resetGroup());
    },
    dispatch,
  })
)(MultipleSelectChip);

export default GroupSplitDialog;

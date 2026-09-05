import Color from 'color';
import PropTypes from 'prop-types';
import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useState,
} from 'react';
import Box from '@material-ui/core/Box';
import ListItem from '@material-ui/core/ListItem';
import { makeStyles } from '@material-ui/core/styles';
import DraggableDialog from '@skybrush/mui-components/lib/DraggableDialog';
import DialogContent from '@material-ui/core/DialogContent';
import MenuItem from '@material-ui/core/MenuItem';
import { Button, Select } from '@material-ui/core';

import { details } from './details';

import {
  InputLabel,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  RadioGroup,
  Radio,
} from '@material-ui/core';

const useStyles = makeStyles((theme) => ({
  input: {
    display: 'none',
  },

  hover: {
    background: theme.palette.action.hover,
  },

  hoverError: {
    background: new Color(theme.palette.error.main).alpha(0.5).string(),
  },
}));

/**
 * List item that triggers a file upload dialog when clicked.
 */
const FileListItem = ({
  accepts,
  children,
  extensions,
  id,
  inputId,
  multiple,
  onSelected,
  onSelectionFailed,
  ...rest
}) => {
  const classes = useStyles();

  // This state variable will be used to force-clear the file input when the
  // user selects a file, then attempts to select it again later. If we did not
  // do this, the second selection would not succeed because no change event
  // would be fired.
  const [generation, setGeneration] = useState(0);
  const [editing, SetEditig] = useState(false);
  const [filenameId, setFileId] = useState('');
  const [position, setPosition] = useState(1);
  const [takeoffPosition, setTakeoffPositionsArray] = useState([]);
  const [options, setOptions] = useState([]);
  const [optName, setOptName] = useState('');
  const [numberofDrones, setNumberOfDrones] = useState([]);
  const [dt, setDT] = useState({ num: 0, time: '0 mins', file: null });
  const [validate, setValidate] = useState(true);

  useLayoutEffect(() => {
    if (!!filenameId && !!position && !!optName && !!dt.num) setValidate(false);
  }, [filenameId, position, dt.num, optName]);

  const onSubmit = () => {
    // if (!accepts(dt.file)) return;
    onHandleSelection(DceRoad);
    SetEditig((prev) => !prev);
  };

  const onHandleSelection = useCallback(
    (item) => {
      if (!item) {
        return;
      }

      if (!accepts || accepts(item)) {
        if (onSelected) {
          onSelected(item);
        }
      } else if (onSelectionFailed) {
        onSelectionFailed(item);
      }
      setGeneration(generation + 1);
    },
    [accepts, multiple, generation, onSelected, onSelectionFailed]
  );

  useEffect(() => {
    const load_position = details.find((file) => file.id === filenameId);
    if (!load_position?.takeoffPosition) return;
    setTakeoffPositionsArray(load_position?.takeoffPosition);
    setOptions(load_position.options);
  }, [filenameId]);

  useEffect(() => {
    const number = options.find((file) => file.name === optName);
    if (!number?.number_of_drones) return;
    setNumberOfDrones(number.number_of_drones);
  }, [optName]);

  // if (position && optName && filenameId && dt.num) setValidate(true);

  return (
    <>
      <label id={id} onClick={() => SetEditig((prev) => !prev)}>
        <ListItem button {...rest}>
          {children}
        </ListItem>
      </label>
      <DraggableDialog
        fullWidth
        open={editing}
        maxWidth='sm'
        title='Choose Runway'
        onClose={() => SetEditig((prev) => !prev)}
      >
        <DialogContent>
          <FormGroup>
            <Box my={2}>
              <FormControl fullWidth variant='filled'>
                <InputLabel id='runway-id'>Select RunWay</InputLabel>
                <Select
                  sx={{ m: 1, maxWidth: 120 }}
                  value={filenameId}
                  labelId='runway-id'
                  onChange={(event) => {
                    setFileId(event.target.value);
                  }}
                >
                  {details.map((item) => (
                    <MenuItem value={item.id} key={`key-${item.id}`}>
                      {item.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {takeoffPosition?.length != 0 && (
                <FormControl
                  fullWidth
                  variant='filled'
                  style={{ marginTop: 5 }}
                >
                  <FormLabel id='form-position' style={{ marginTop: 20 }}>
                    Select position
                  </FormLabel>
                  <RadioGroup aria-labelledby='form-position' row>
                    {takeoffPosition?.length != 0 &&
                      takeoffPosition.map((pos) => (
                        <FormControlLabel
                          label={pos}
                          value={pos}
                          control={<Radio checked={position == pos} />}
                          onChange={() => setPosition(pos)}
                        />
                      ))}
                  </RadioGroup>
                </FormControl>
              )}
              {options?.length != 0 && (
                <FormControl
                  fullWidth
                  variant='filled'
                  style={{ marginTop: 5 }}
                >
                  <FormLabel id='form-position' style={{ marginTop: 20 }}>
                    Select RunWay Type
                  </FormLabel>
                  <RadioGroup aria-labelledby='form-position' row>
                    {options?.length != 0 &&
                      options.map((option) => (
                        <FormControlLabel
                          label={option.name}
                          value={option.name}
                          control={<Radio checked={optName == option.name} />}
                          onChange={() => setOptName(option.name)}
                        />
                      ))}
                  </RadioGroup>
                </FormControl>
              )}
              {numberofDrones?.length != 0 && (
                <FormControl
                  fullWidth
                  variant='filled'
                  style={{ marginTop: 5 }}
                >
                  <FormLabel id='form-position' style={{ marginTop: 20 }}>
                    Select Number of Drones
                  </FormLabel>
                  {numberofDrones?.length != 0 &&
                    numberofDrones.map((item) => (
                      <FormControlLabel
                        label={item.num}
                        value={item.num}
                        control={<Radio checked={dt.num === item.num} />}
                        onChange={() =>
                          setDT(() => {
                            return {
                              num: item.num,
                              time: item.time,
                              file: item.file,
                            };
                          })
                        }
                      />
                    ))}
                </FormControl>
              )}
            </Box>
            <Button disabled={false} onClick={onSubmit} variant='contained'>
              Submit
            </Button>
          </FormGroup>
          <h3>Time taken to complete mission: {dt.time}</h3>
        </DialogContent>
      </DraggableDialog>
    </>
  );
};

FileListItem.propTypes = {
  accepts: PropTypes.func,
  children: PropTypes.node,
  extensions: PropTypes.arrayOf(PropTypes.string),
  id: PropTypes.string,
  inputId: PropTypes.string.isRequired,
  multiple: PropTypes.bool,
  onSelected: PropTypes.func,
  onSelectionFailed: PropTypes.func,
};

export default (props) => {
  return <FileListItem {...props} />;
};

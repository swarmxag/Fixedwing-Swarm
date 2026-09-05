import React, { useState } from 'react';
import config from 'config';
import {
  InputLabel,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Button,
  Radio,
  MenuItem,
  Box,
  Select,
  Input,
  RadioGroup,
} from '@material-ui/core';

const StrikePanel = () => {
  const [MSG, setMSG] = useState({
    id: 1,
    latitude: 0.0,
    longitude: 0.0,
    withRTL: false,
  });

  const url = config['strike_url'];

  const handleSubmit = () => {
    const req_url = url[MSG.id - 1];
    if (!MSG.latitude && !MSG.longitude) {
      console.log(MSG.latitude);
    }
    console.log(req_url, MSG);
  };

  const handleAbort = () => {
    console.log('Abort');
  };

  return (
    <Box style={{ margin: 10, gap: 20 }}>
      <FormGroup style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <FormControl fullWidth variant='standard'>
            <InputLabel id='drone-id'>Choose Drone:</InputLabel>
            <Select
              style={{ padding: 5 }}
              value={MSG.id}
              labelId='drone-id'
              onChange={({ target: { value } }) =>
                setMSG((prev) => {
                  return { ...prev, id: value };
                })
              }
            >
              {url?.length != 0 &&
                url.map((item) => (
                  <MenuItem value={item.id}>{item.id}</MenuItem>
                ))}
            </Select>
          </FormControl>
        </Box>
        <Box style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <FormControl fullWidth variant='standard'>
            <InputLabel id='drone-id'>Target Latitude:</InputLabel>
            <Input
              style={{ padding: 5 }}
              type='number'
              value={MSG.latitude}
              onChange={({ target: { value } }) =>
                setMSG((prev) => {
                  return { ...prev, latitude: value };
                })
              }
            />
          </FormControl>
          <FormControl fullWidth variant='standard'>
            <InputLabel id='drone-id'>Target Longitude:</InputLabel>
            <Input
              style={{ padding: 5 }}
              type='number'
              value={MSG.longitude}
              onChange={({ target: { value } }) =>
                setMSG((prev) => {
                  return { ...prev, longitude: value };
                })
              }
            />
          </FormControl>
        </Box>

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
          <FormLabel id='form-position'>RTL :</FormLabel>
          <RadioGroup aria-labelledby='form-position' row>
            <FormControlLabel
              label={'With RTL'}
              control={<Radio checked={MSG.withRTL} />}
              onChange={() =>
                setMSG((prev) => {
                  return { ...prev, withRTL: true };
                })
              }
            />
            <FormControlLabel
              label={'Without RTL'}
              control={<Radio checked={!MSG.withRTL} />}
              onChange={() =>
                setMSG((prev) => {
                  return { ...prev, withRTL: false };
                })
              }
            />
          </RadioGroup>
        </FormControl>
        <Button onClick={handleSubmit} variant='contained'>
          Submit
        </Button>
        <Button onClick={handleAbort} variant='contained'>
          Abort
        </Button>
      </FormGroup>
    </Box>
  );
};

export default StrikePanel;

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

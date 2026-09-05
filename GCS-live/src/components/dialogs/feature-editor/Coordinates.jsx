import PropTypes from 'prop-types';
import React, { useState } from 'react';
import { FormControl, TextField } from '@material-ui/core';

const Coordinates = ({
  value,
  optimizeUIForTouch,
  index,
  Latitude,
  Longitude,
}) => {
  return (
    <FormControl
      variant='standard'
      style={{
        display: 'flex',
        flexDirection: 'row',
        gap: 15,
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <TextField
        fullWidth
        autoFocus={!optimizeUIForTouch}
        label='Latitude'
        variant='filled'
        value={value[1] || ''}
        onChange={({ target: { value } }) => Latitude(index, value)}
      />
      <TextField
        fullWidth
        autoFocus={!optimizeUIForTouch}
        label='Longitude'
        variant='filled'
        value={value[0] || ''}
        onChange={({ target: { value } }) => Longitude(index, value)}
      />
    </FormControl>
  );
};

Coordinates.propTypes = {
  value: PropTypes.string.isRequired,
  optimizeUIForTouch: PropTypes.bool.isRequired,
  index: PropTypes.number,
  Latitude: PropTypes.func,
  Longitude: PropTypes.func,
};

export default Coordinates;

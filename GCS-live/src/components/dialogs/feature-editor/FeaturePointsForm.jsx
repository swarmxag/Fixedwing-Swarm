import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import { shouldOptimizeUIForTouch } from '~/features/settings/selectors';
import { Box } from '@material-ui/core';
import Coordinates from './Coordinates';
import { setLatitude, setLongitude } from '~/features/map-features/slice';

const FeaturePointsForm = ({
  feature,
  optimizeUIForTouch,
  Latitude,
  Longitude,
}) => {
  return (
    <Box
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        marginTop: 10,
      }}
    >
      {feature.points.map((item, i) => (
        <Coordinates
          value={item}
          Latitude={Latitude}
          Longitude={Longitude}
          optimizeUIForTouch={optimizeUIForTouch}
          index={i}
        />
      ))}
    </Box>
  );
};

FeaturePointsForm.propTypes = {
  feature: PropTypes.object.isRequired,
  featureId: PropTypes.string.isRequired,
  optimizeUIForTouch: PropTypes.bool.isRequired,
  Latitude: PropTypes.func,
  Longitude: PropTypes.func,
};

export default connect(
  // mapStateToProps
  (state, { featureId }) => ({
    optimizeUIForTouch: shouldOptimizeUIForTouch(state),
  }),
  // mapDispatchToProps
  (dispatch, { featureId }) => ({
    Latitude: (index, latitude) =>
      dispatch(setLatitude({ id: featureId, index, latitude })),
    Longitude: (index, longitude) =>
      dispatch(setLongitude({ id: featureId, index, longitude })),
  })
)(FeaturePointsForm);

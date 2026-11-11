import { Circle, Style, Text } from 'ol/style';

import { Feature, geom, layer as olLayer, source } from '@collmot/ol-react';
import PropTypes from 'prop-types';
import React, { useCallback } from 'react';
import { connect } from 'react-redux';

import Header from '@skybrush/mui-components/lib/FormHeader';

import ActiveUAVsLayerSource from '../sources/ActiveUAVsLayerSource';

import SwatchesColorPicker from '~/components/SwatchesColorPicker';
import { setLayerParametersById } from '~/features/map/layers';
import flock from '~/flock';
import { shouldShowHomeLocations } from '~/features/settings/selectors';
import { getUAVsWithHomeLocation } from '~/features/uavs/selectors';
import { getSelection } from '~/selectors/selection';
import { mapViewCoordinateFromLonLat } from '~/utils/geography';
import { fill, stroke } from '~/utils/styles';

// === Settings for this particular layer type ===

const UAVsLayerSettingsPresentation = ({ layer, setLayerParameters }) => {
  const { parameters } = layer;
  const { labelColor } = parameters || {};

  const onColorChanged = useCallback(
    (color) => {
      setLayerParameters({ labelColor: color.hex });
    },
    [setLayerParameters]
  );

  return (
    <>
      <Header>Label color</Header>
      <SwatchesColorPicker
        color={labelColor || '#000000'}
        onChangeComplete={onColorChanged}
      />
    </>
  );
};

UAVsLayerSettingsPresentation.propTypes = {
  layer: PropTypes.object,
  setLayerParameters: PropTypes.func,
};

export const UAVsLayerSettings = connect(
  // mapStateToProps
  null,
  // mapDispatchToProps
  (dispatch, ownProps) => ({
    setLayerParameters(parameters) {
      dispatch(setLayerParametersById(ownProps.layerId, parameters));
    },
  })
)(UAVsLayerSettingsPresentation);

// === The actual layer to be rendered ===

const homeMarkerStyle = (feature) =>
  new Style({
    image: new Circle({
      fill: fill('#ffffff'),
      radius: 7,
      stroke: stroke('#d81b60', 3),
    }),
    text: new Text({
      font: 'bold 12px sans-serif',
      offsetY: 18,
      text: `H ${feature.get('uavId')}`,
      textAlign: 'center',
      fill: fill('#d81b60'),
      stroke: stroke('#ffffff', 3),
    }),
  });

/**
 * Markers for the autopilot-reported home locations of the UAVs when enabled in
 * the display preferences.
 */
const HomeLocationsPresentation = ({ homes, projection, zIndex }) =>
  homes.length > 0 ? (
    <olLayer.Vector zIndex={zIndex}>
      <source.Vector>
        {homes.map(({ uavId, lat, lon }) => (
          <Feature
            key={`home.${uavId}`}
            id={`home$${uavId}`}
            properties={{ uavId }}
            style={homeMarkerStyle}
          >
            <geom.Point coordinates={projection([lon, lat])} />
          </Feature>
        ))}
      </source.Vector>
    </olLayer.Vector>
  ) : null;

HomeLocationsPresentation.propTypes = {
  homes: PropTypes.arrayOf(
    PropTypes.shape({
      uavId: PropTypes.string,
      lat: PropTypes.number,
      lon: PropTypes.number,
    })
  ).isRequired,
  projection: PropTypes.func.isRequired,
  zIndex: PropTypes.number,
};

const NO_HOMES = [];

const HomeLocations = connect((state) => ({
  homes: shouldShowHomeLocations(state)
    ? getUAVsWithHomeLocation(state)
    : NO_HOMES,
}))(HomeLocationsPresentation);

const UAVsLayerPresentation = ({ layer, projection, selection, zIndex }) => (
  <>
    <HomeLocations projection={projection} zIndex={zIndex} />
    <olLayer.Vector updateWhileAnimating updateWhileInteracting zIndex={zIndex}>
      <ActiveUAVsLayerSource
        selection={selection}
        labelColor={layer.parameters.labelColor}
        flock={flock}
        projection={projection}
      />
    </olLayer.Vector>
  </>
);

UAVsLayerPresentation.propTypes = {
  layer: PropTypes.object,
  zIndex: PropTypes.number,

  selection: PropTypes.arrayOf(PropTypes.string).isRequired,
  projection: PropTypes.func,
};

UAVsLayerPresentation.defaultProps = {
  projection: mapViewCoordinateFromLonLat,
};

export const UAVsLayer = connect(
  // mapStateToProps
  (state) => ({
    selection: getSelection(state),
  }),
  // mapDispatchToProps
  {}
)(UAVsLayerPresentation);

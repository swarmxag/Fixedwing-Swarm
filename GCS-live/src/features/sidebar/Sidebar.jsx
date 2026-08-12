/* global VERSION */

import Box from '@material-ui/core/Box';
import Typography from '@material-ui/core/Typography';
import Flight from '@material-ui/icons/Flight';
import Layers from '@material-ui/icons/Layers';
import Map from '@material-ui/icons/Map';
import Place from '@material-ui/icons/Place';
import { CameraAltRounded } from '@material-ui/icons';
import Grain from '@material-ui/icons/Grain';

import PropTypes from 'prop-types';
import React from 'react';
import { withTranslation } from 'react-i18next';
import { Module, ModuleTray, Workbench } from 'react-flexible-workbench';
import { connect } from 'react-redux';

import { areExperimentalFeaturesEnabled } from '~/features/settings/selectors';
import ShapeLine from '~/icons/ShapeLine';
import { hasFeature } from '~/utils/configuration';

import { isSidebarOpen } from './selectors';
import SwarmIcon from './SwarmIcon';
import { ClockView } from '@material-ui/pickers';

// NOTE: The scrollbar is not only OS dependent, but also browser dependent.
const SIDEBAR_OPEN_WIDTH = 180; /* 160px is enough for most platforms, but apparently Windows needs 180px because of the scrollbar */

const style = {
  backgroundColor: '#333',
  boxShadow: 'rgba(0, 0, 0, 0.3) -9px -3px 6px -6px inset',
  display: 'flex',
  flexFlow: 'column nowrap',
  height: 'calc(100vh - 48px)',
  overflow: 'hidden',
};

const innerStyle = {
  display: 'flex',
  flexFlow: 'column nowrap',
  flexGrow: 1,
  overflow: 'auto',
  width: SIDEBAR_OPEN_WIDTH,
};

const hasShowControl = hasFeature('showControl');

/**
 * Presentation component for the sidebar at the left edge of the main
 * window.
 *
 * @returns  {Object}  the rendered sidebar component
 */
const Sidebar = ({ experimentalFeaturesEnabled, isOpen, t, workbench }) => (
  <div
    id='sidebar'
    style={{ ...style, width: isOpen ? SIDEBAR_OPEN_WIDTH : 48 }}
  >
    <div style={innerStyle}>
      <ModuleTray allowMultipleSelection vertical workbench={workbench}>
        <Module id='map' icon={<Map />} label={t('view.map')} component='map' />
        <Module
          id='layers'
          icon={<Layers />}
          label={t('view.layer-list')}
          component='layer-list'
        />
        {hasFeature('mapFeatures') && (
          <Module
            id='features'
            icon={<ShapeLine />}
            label={t('view.feature-list')}
            component='feature-list'
          />
        )}
        <Module
          id='uavs'
          icon={<Flight />}
          label={t('view.uav-list')}
          component='uav-list'
        />
        <hr />
        {/* Do not use a single React fragment here for the next section; it would confuse `react-flexible-workbench` */}
        <Module
          id='camera'
          icon={<CameraAltRounded />}
          label={t('view.camera')}
          component='camera'
        />
        <Module
          id='spare-drone'
          icon={<CameraAltRounded />}
          label='Video Panel'
          component='spare'
        />
        <Module
          id='locations'
          icon={<Place />}
          label={t('view.saved-location-list')}
          component='saved-location-list'
        />
        {/* <Module
          label={'clock'}
          component='lcd-clock-panel'
          icon={<Grain />}
          id='clock'
        /> */}
        <Module
          id='vtol'
          icon={<SwarmIcon />}
          label={'VTOL Swarm'}
          component='vtol'
        />
        <Module
          id='swarm'
          icon={<SwarmIcon />}
          label={'Swarm Panel'}
          component='swarm'
        />
        <Module
          id='simulator'
          icon={<SwarmIcon />}
          label={'Simulator Panel'}
          component='simulator'
        />
        <Module
          id={'strike'}
          icon={<SwarmIcon />}
          component={'strike'}
          label={'Strike Panel'}
        />
      </ModuleTray>
    </div>
    {isOpen && (
      <Box
        py={0.5}
        px={1}
        style={{ color: '#fff', opacity: 0.3, width: SIDEBAR_OPEN_WIDTH }}
      >
        <Typography align='center' variant='caption' component='footer'>
          {VERSION}
        </Typography>
      </Box>
    )}
  </div>
);

Sidebar.propTypes = {
  experimentalFeaturesEnabled: PropTypes.bool,
  isOpen: PropTypes.bool,
  t: PropTypes.func,
  workbench: PropTypes.instanceOf(Workbench).isRequired,
};

/**
 * Sidebar at the left edge of the main window.
 */
export default connect(
  // mapStateToProps
  (state, { workbench }) => ({
    experimentalFeaturesEnabled: areExperimentalFeaturesEnabled(state),
    isOpen: isSidebarOpen(state),
    workbench,
  })
)(withTranslation()(Sidebar));

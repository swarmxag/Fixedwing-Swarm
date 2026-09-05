import clsx from 'clsx';
import PropTypes from 'prop-types';
import React from 'react';

import CircularProgress from '@material-ui/core/CircularProgress';
import { makeStyles } from '@material-ui/core/styles';
import { Colors, Status } from '@skybrush/app-theme-material-ui';
import SemanticAvatar from '@skybrush/mui-components/lib/SemanticAvatar';

import { BatteryFormatter } from '~/components/battery';
import BatteryIndicator from '~/components/BatteryIndicator';
import StatusPill from '~/components/StatusPill';

import SecondaryStatusLight from './SecondaryStatusLight';
import store from '~/store';
import alertSoundResource from '~/../assets/sounds/alert.mp3';
import { useAudio, useInterval, useMount } from 'react-use';
import { showError } from '~/features/snackbar/actions';

const AUDIO_REPEAT_INTERVAL_SEC = 2;

const AlertSound = () => {
  const [audio, state, controls] = useAudio(<audio src={alertSoundResource} />);

  // Trigger audio first when the component is mounted
  useMount(() => controls.play());

  // Also trigger audio every AUDIO_REPEAT_INTERVAL_SEC seconds
  useInterval(() => {
    if (!state.playing) {
      controls.play();
    }
  }, AUDIO_REPEAT_INTERVAL_SEC * 1000);

  return audio;
};

const useStyles = makeStyles(
  (theme) => ({
    avatarWrapper: {
      position: 'relative',
      '&:not(:last-child)': {
        marginBottom: theme.spacing(0.5),
      },


      '&::after': {
        background: Colors.error,
        boxShadow:
          '1px 1px 4px rgba(0, 0, 0, 0.6), 1px 1px 2px rgba(255, 255, 255, 0.3) inset',
        content: '""',
        height: 4,
        left: '50%',
        position: 'absolute',
        top: 'calc(50% - 2px)',
        transform: 'rotate(-45deg)',
        transition: 'left 300ms, width 300ms',
        width: '0%',
      },

      '&.crossed::after': {
        left: '-20%',
        width: '140%',
      },
    },

    avatarContent: {
      width: '100%',
      textAlign: 'center',
    },

    gone: {
      opacity: 0.7,
    },

    hint: {
      fontSize: '0.75rem',
    },

    hintSeparator: {
      width: '75%',

      marginTop: 0,
      marginBottom: 2,

      border: '1px solid',
      borderBottomWidth: 0,

      opacity: 0.6,

      color: 'inherit',
    },

    progress: {
      position: 'absolute',
      top: -2,
      left: -2,
    },
  }),
  { name: 'ComplexAvatar' }
);

/**
 * Avatar that represents a single drone, docking station or some other object
 * in the system that has an ID.
 */

const ComplexAvatar = ({
  AvatarProps,
  batteryFormatter,
  batteryStatus,
  hint,
  crossed,
  details,
  editing,
  gone,
  id,
  label,
  progress,
  secondaryStatus,
  status,
  text,
  textSemantics,
  airspeed,
  height,
  mode,
  shouldPlayAlert,
}) => {
  let err = '';
  // const airspeedThreshold = store.getState().settings.uavs.airspeedThreshold;
  const classes = useStyles();

  return (
    <>
      <div
        className={clsx(
          classes.avatarWrapper,
          crossed && 'crossed',
          gone && classes.gone
        )}
      >
        {shouldPlayAlert && <AlertSound />}
        <SemanticAvatar
          status={editing ? Status.NEXT : status}
          {...AvatarProps}
        >
          <div className={classes.avatarContent}>
            {label === undefined ? id : label}
          </div>
        </SemanticAvatar>
        {progress > 0 && (
          <CircularProgress
            className={classes.progress}
            size={44}
            value={progress}
            variant='static'
          />
        )}
        {secondaryStatus && <SecondaryStatusLight status={secondaryStatus} />}
      </div>
      {height && <StatusPill status={textSemantics}>{height}</StatusPill>}
      {airspeed && (
        <StatusPill status={textSemantics}>{airspeed} m/s</StatusPill>
      )}
      {(details || text) && (
        <StatusPill status={textSemantics}>{details || text}</StatusPill>
      )}
      <StatusPill status={textSemantics}>{err}</StatusPill>
      {mode && <StatusPill status={textSemantics}>{mode}</StatusPill>}
      {batteryStatus && (
        <BatteryIndicator formatter={batteryFormatter} {...batteryStatus} />
      )}
    </>
  );
};

ComplexAvatar.propTypes = {
  AvatarProps: PropTypes.object,
  batteryFormatter: PropTypes.instanceOf(BatteryFormatter),
  batteryStatus: PropTypes.shape({
    cellCount: PropTypes.number,
    voltage: PropTypes.number,
    percentage: PropTypes.number,
  }),
  hint: PropTypes.string,
  crossed: PropTypes.bool,
  details: PropTypes.string,
  editing: PropTypes.bool,
  gone: PropTypes.bool,
  id: PropTypes.string,
  label: PropTypes.string,
  progress: PropTypes.number,
  secondaryStatus: PropTypes.oneOf([
    'off',
    'info',
    'success',
    'warning',
    'rth',
    'error',
    'critical',
  ]),
  selected: PropTypes.bool,
  status: PropTypes.oneOf([
    'off',
    'info',
    'success',
    'warning',
    'rth',
    'error',
    'critical',
  ]),
  text: PropTypes.string,
  textSemantics: PropTypes.oneOf([
    'off',
    'info',
    'success',
    'warning',
    'rth',
    'error',
    'critical',
  ]),
};

ComplexAvatar.defaultProps = {
  status: 'off',
  textSemantics: 'info',
};

export default ComplexAvatar;

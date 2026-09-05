import isNil from 'lodash-es/isNil';
import PropTypes from 'prop-types';
import React, { useEffect } from 'react';
import { connect } from 'react-redux';
import { useHarmonicIntervalFn, useUpdate } from 'react-use';
import { showNotification } from '~/features/snackbar/actions';
import { MessageSemantics } from '~/features/snackbar/types';
import store from '~/store';
import { getClockById } from '~/features/clocks/selectors';
import {
  formatTicksOnClock,
  getTickCountOnClockAt,
  getPreferredUpdateIntervalOfClock,
  isClockAffectedByClockSkew,
  isClockSigned,
} from '~/features/clocks/utils';
import { getRoundedClockSkewInMilliseconds } from '~/features/servers/selectors';
import flock from '~/flock';

const ClockDisplayLabel = ({
  affectedByClockSkew,
  clock,
  clockId,
  clockSkew,
  emptyText,
  format,
  signed,
  updateInterval,
  ...rest
}) => {
  const { running, ticksPerSecond } = clock || {};
  const uavs = flock.getAllUAVs();

  useEffect(() => {
    // if (uavs?.length == 0) return;
    const intervalId = setInterval(() => {
      store.dispatch(
        showNotification({
          message: `${uavs?.length}`,
          semantics: MessageSemantics.SUCCESS,
        })
      );
    }, 1000);
    return () => clearInterval(intervalId);
  }, []);

  const timestamp =
    Date.now() + (affectedByClockSkew && !isNil(clockSkew) ? clockSkew : 0);
  const ticks = clock ? getTickCountOnClockAt(clock, timestamp) : undefined;
  const formattedTime =
    ticks === undefined
      ? emptyText
      : formatTicksOnClock(ticks, clock, { format });
  const update = useUpdate();
  let seconds = ticks / ticksPerSecond;
  useHarmonicIntervalFn(update, running ? updateInterval : null);

  let average_coverage = 3 * seconds;

  return (
    <div>
      Coverage Area Percentage {average_coverage}
      <div>
        <span {...rest}>{formattedTime}</span>
      </div>
    </div>
  );
};

ClockDisplayLabel.propTypes = {
  affectedByClockSkew: PropTypes.bool,
  clock: PropTypes.object,
  clockId: PropTypes.string,
  clockSkew: PropTypes.number,
  emptyText: PropTypes.string,
  format: PropTypes.string,
  signed: PropTypes.bool,
  updateInterval: PropTypes.number,
};

ClockDisplayLabel.defaultProps = {
  format: 'HH:mm:ss',
};

export default connect(
  // mapStateToProps
  (state, ownProps) => {
    const clock = getClockById(state, ownProps.clockId);
    const signed = isClockSigned(clock);
    const affectedByClockSkew = isClockAffectedByClockSkew(clock);
    const updateInterval = getPreferredUpdateIntervalOfClock(clock);
    const clockSkew = getRoundedClockSkewInMilliseconds(state);
    return { affectedByClockSkew, clock, clockSkew, signed, updateInterval };
  },
  // mapDispatchToProps
  {}
)(ClockDisplayLabel);

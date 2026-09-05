/**
 * @file Component for displaying logged messages.
 */

import PropTypes from 'prop-types';
import React, { useEffect } from 'react';
import { connect } from 'react-redux';

import { addTextLog } from '~/features/log/slice';

import LogMessageList from './LogMessageList';
import messageHub from '~/message-hub';
import { getCurrentServerState } from '~/features/servers/selectors';
import { ConnectionState } from '~/model/enums';

const LogPanel = ({ items, addTextLog, connectionState }) => {
  useEffect(() => {
    if (!(connectionState == ConnectionState.CONNECTED)) return;
    const intervalId = setInterval(() => {
      (async () => {
        const res = await messageHub.sendMessage({
          type: 'X-UAV-socket',
          message: 'log',
        });
        addTextLog(res.body.message);
      })();
    }, 500);
    return () => clearInterval(intervalId);
  }, [connectionState == ConnectionState.CONNECTED]);

  return <LogMessageList items={items} />;
};

LogPanel.propTypes = {
  items: PropTypes.array,
  updateLogPanelVisibility: PropTypes.func.isRequired,
};

export default connect(
  // mapStateToProps
  (state) => ({
    items: state.log.socketItems,
    connectionState: getCurrentServerState(state).state,
  }),
  // mapDispatchToProps
  {
    addTextLog,
  }
)(LogPanel);

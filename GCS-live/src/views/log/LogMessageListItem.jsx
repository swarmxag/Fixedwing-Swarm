import PropTypes from 'prop-types';
import React from 'react';

import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
  root: {
    display: 'flex',
    padding: theme.spacing(0, 1),
    alignItems: 'stretch',
    borderBottom: `1px solid ${theme.palette.divider}`,
    cursor: 'default',

    '&:hover': {
      backgroundColor: theme.palette.action.hover,
    },
  },

  statusLight: {
    paddingTop: 2,
    width: 20,
  },

  timestamp: {
    color: theme.palette.text.secondary,
    paddingRight: theme.spacing(1),
    width: 56,
    textAlign: 'right',
  },

  module: {
    color: theme.palette.primary[500],
    overflow: 'hidden',
    paddingRight: theme.spacing(1),
    textOverflow: 'ellipsis',
    width: 96,
  },

  auxiliaryId: {
    color: theme.palette.text.secondary,
    overflow: 'hidden',
    paddingRight: theme.spacing(1),
    textOverflow: 'ellipsis',
    width: 80,
  },

  moduleExtended: {
    color: theme.palette.primary[500],
    overflow: 'hidden',
    paddingRight: theme.spacing(1),
    textOverflow: 'ellipsis',
    width: 96 + 80,
  },

  message: {
    flex: 1,
    overflow: 'hidden',
    whiteSpace: 'noWrap',
  },
}));

const LogMessageListItem = React.memo(({ item }) => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div className={classes.timestamp}>{item?.timestamp}</div>
      <div className={classes.message}>{item?.message}</div>
    </div>
  );
});

LogMessageListItem.propTypes = {
  item: PropTypes.shape({
    level: PropTypes.number,
    message: PropTypes.string,
    module: PropTypes.string,
    timestamp: PropTypes.number,
    auxiliaryId: PropTypes.string,
  }),
};

export default LogMessageListItem;

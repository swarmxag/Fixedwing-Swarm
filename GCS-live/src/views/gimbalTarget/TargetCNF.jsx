import React from 'react';
import { connect } from 'react-redux';
import { getTargetCNF } from '~/features/target/selectors';
import { removetargetCNF } from '~/features/target/slice';
import {
  Button,
  Box,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
} from '@material-ui/core';
import { Done } from '@material-ui/icons';
import { TooltipWithContainerFromContext as Tooltip } from '~/containerContext';

const TaregtCNF = ({ target, removeTarget }) => {
  return (
    <Box>
      {target?.length > 0 ? (
        target.map((tar) => (
          <ListItem button onClick={() => {}}>
            <ListItemText primary={`${tar.lat} ${tar.lon}`} />
            <IconButton onClick={removeTarget.bind(this, tar.id)}>
              <Done />
            </IconButton>
          </ListItem>
          //   <ListItem button onClick={() => {}}>
          //     <ListItemText primary={`${tar.lat} ${tar.lon}`} />
          //     <ListItemSecondaryAction>{actionButton}</ListItemSecondaryAction>
          //   </ListItem>
        ))
      ) : (
        <div>No Target Coordinates receive from the gimbal</div>
      )}
    </Box>
  );
};

export default connect(
  (state) => ({
    target: getTargetCNF(state),
  }),
  (dispatch) => ({
    removeTarget(id) {
      dispatch(removetargetCNF(id));
    },
  })
)(TaregtCNF);

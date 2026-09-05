import React, { Fragment, useState, useRef, useEffect } from 'react';
import {
  MenuItem,
  Select,
  Button,
  FormControl,
  InputLabel,
  Input,
} from '@material-ui/core';
import messageHub from '~/message-hub';
import store from '~/store';
import { showNotification } from '~/features/snackbar/actions';
import { MessageSemantics } from '~/features/snackbar/types';
import LongPressButton from '~/components/button/LongPressButton';

const isAppsink = Boolean(window.bridge?.getGstPipeline);

const { dispatch } = store;

const SpareDronePanel = () => {
  const [gimbal, setGimbal] = useState('');
  const [gimbalControl, setGimbalControl] = useState();
  const [record, setRecording] = useState(false);
  const imgRef = useRef(null);

  // useEffect(() => {
  //   (async () => {
  //     if (isAppsink) {
  //       await window.bridge?.getGstPipeline();
  //     }
  //   })();
  // }, []);

  const onCameraChange = async ({ target }) => {};

  const onButtonPress = async (msg) => {
    // if (allCamera) return;
    try {
      const res = await messageHub.sendMessage({
        type: 'X-Camera-MISSION',
        message: msg,
        ip: '',
      });

      if (!Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `${msg} Message Failed`,
            semantics: MessageSemantics.ERROR,
          })
        );
      }
    } catch (e) {
      dispatch(
        showNotification({
          message: `${e} Command is Failed`,
          semantics: MessageSemantics.ERROR,
        })
      );
    }
  };

  const handleDoubleClick = async (event) => {
    const img = imgRef.current;
    if (!img) return;

    const rect = img.getBoundingClientRect();

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    // Calculate center
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Custom coordinate system: center is (0,0)
    const customX = x - centerX; // Right is negative, Left is positive
    const customY = y - centerY; // Up is negative, Down is positive

    try {
      const res = await messageHub.sendMessage({
        type: 'X-Camera-MISSION',
        message: 'track',
        x: customX,
        y: customY,
        ip: '192.168.0.119',
      });
      if (!Boolean(res?.body?.message)) {
        dispatch(
          showNotification({
            message: `Track Message Failed`,
            semantics: MessageSemantics.ERROR,
          })
        );
      } else {
        if (!Boolean(res?.body?.message)) {
          dispatch(
            showNotification({
              message: `Track Message Success`,
              semantics: MessageSemantics.SUCCESS,
            })
          );
        }
      }
    } catch (e) {
      dispatch(
        showNotification({
          message: `${e} Command is Failed`,
          semantics: MessageSemantics.ERROR,
        })
      );
    }
  };

  return (
    <Fragment>
      <div
        style={{
          display: 'flex',
          alignSelf: 'center',
          gap: 10,
        }}
      >
        <FormControl>
          <InputLabel id='demo-simple-select-label'>Ip</InputLabel>
          <Input value={gimbal} onChange={() => {}} />
          {/* <Select
            id='demo-simple-select-label'
            onChange={onCameraChange}
            value={gimbal}
          >
            {video.map(({ id, ip, name, url }) => (
              <MenuItem value={ip} name={url}>
                {ip}
              </MenuItem>
            ))}
          </Select> */}
        </FormControl>
        <Button
          onClick={async () => {
            if (isAppsink) {
              await window.bridge?.getGstPipeline();
            }
          }}
        >
          Start Camera
        </Button>
        <LongPressButton
          onLongPress={onButtonPress.bind(this, 'zoom_in')}
          onLongPressEnd={onButtonPress.bind(this, 'zoom_stop')}
        >
          Zoom in
        </LongPressButton>
        <LongPressButton
          onLongPress={onButtonPress.bind(this, 'zoom_out')}
          onLongPressEnd={onButtonPress.bind(this, 'zoom_stop')}
        >
          Zoom out
        </LongPressButton>
        <LongPressButton
          onLongPress={onButtonPress.bind(this, 'up')}
          onLongPressEnd={onButtonPress.bind(this, 'stop')}
        >
          Up
        </LongPressButton>
        <LongPressButton
          onLongPress={onButtonPress.bind(this, 'left')}
          onLongPressEnd={onButtonPress.bind(this, 'stop')}
        >
          Left
        </LongPressButton>
        <Button onClick={onButtonPress.bind(this, 'home')}>HOME</Button>
        <LongPressButton
          onLongPress={onButtonPress.bind(this, 'right')}
          onLongPressEnd={onButtonPress.bind(this, 'stop')}
        >
          RIGHT
        </LongPressButton>
        <LongPressButton
          onLongPress={onButtonPress.bind(this, 'down')}
          onLongPressEnd={onButtonPress.bind(this, 'stop')}
        >
          Down
        </LongPressButton>
        <Button
          onClick={() => {
            onButtonPress('start_record');
            setRecording(true);
          }}
        >
          Start Recording
        </Button>
        <Button
          onClick={() => {
            onButtonPress('stop_record');
            setRecording(false);
          }}
        >
          Stop Recording
        </Button>
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <img
          ref={imgRef}
          src='http://localhost:9000/stream'
          style={{}}
          // src={require('../../../assets/error.jpg')}
          alt='RTSP Stream'
          onDoubleClick={handleDoubleClick}
        />
      </div>
    </Fragment>
  );
};

export default SpareDronePanel;

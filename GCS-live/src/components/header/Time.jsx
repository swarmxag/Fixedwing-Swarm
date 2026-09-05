import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';
import { setTimerRunning } from '~/features/swarm/slice';

const Timer = ({ isRunning, stopTimer }) => {
  const [time, setTime] = useState(0); // Time in seconds

  // useEffect(() => {
  //   let timer;

  //   if (isRunning) {
  //     timer = setInterval(() => {
  //       setTime((prevTime) => prevTime + 1);
  //     }, 1000);
  //   } else {
  //     clearInterval(timer);
  //   }

  //   return () => clearInterval(timer); // Cleanup on unmount
  // }, [isRunning]);

  // Function to format time into hh:mm:ss
  const formatTime = (seconds) => {
    const hrs = String(Math.floor(seconds / 3600)).padStart(2, '0');
    const mins = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
    const secs = String(seconds % 60).padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
  };

  return (
    <div
      style={{
        marginLeft: '4rem',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}
    >
      <div>
        <h1>{formatTime(time)}</h1>
      </div>
      <button onClick={stopTimer} disabled={!isRunning}>
        Stop
      </button>
      <button
        onClick={() => {
          setTime(0);
          stopTimer();
        }}
      >
        Reset
      </button>
    </div>
  );
};

export default connect(
  // mapStateToProps
  (state) => ({
    isRunning: state.socket.timerRunning,
  }),
  // mapDispatchToProps
  (dispatch) => ({
    stopTimer: () => dispatch(setTimerRunning(false)),
  })
)(Timer);

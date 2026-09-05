import React, { useState, useRef } from 'react';
import { Button } from '@material-ui/core';

const LongPressButton = ({
  onLongPress,
  onLongPressEnd,
  children,
  onClick,
  disabled,
}) => {
  const [isPressing, setIsPressing] = useState(false);
  const timerRef = useRef(null);

  const handleMouseDown = () => {
    setIsPressing(true);
    timerRef.current = setTimeout(() => {
      onLongPress();
    }, 300); // Long press duration (500ms)
  };

  const handleMouseUp = () => {
    if (isPressing) {
      clearTimeout(timerRef.current);
      setIsPressing(false);
      onLongPressEnd();
    }
  };

  const handleMouseLeave = () => {
    if (isPressing) {
      clearTimeout(timerRef.current);
      setIsPressing(false);
      onLongPressEnd();
    }
  };

  return (
    <Button
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleMouseDown}
      onTouchEnd={handleMouseUp}
      variant='text'
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </Button>
  );
};

export default LongPressButton;

// const App = () => {
//   const handleLongPress = () => {
//     console.log('Long press started');
//   };

//   const handleLongPressEnd = () => {
//     console.log('Long press ended');
//   };

//   return (
//     <div>
//       <LongPressButton onLongPress={handleLongPress} onLongPressEnd={handleLongPressEnd}>
//         Press and Hold
//       </LongPressButton>
//     </div>
//   );
// };

// export default App;

import React, { useEffect } from 'react';
import { openOnLoadImage } from '~/features/show/slice';
import { connect, useDispatch, useSelector } from 'react-redux';
import store from '~/store';
import { Button, Box, Typography } from '@material-ui/core';
import { showError } from '~/features/snackbar/actions';
import {
  setImageNames,
  toggleImageSelection,
  selectAllImages,
  clearImageSelection,
} from '~/features/Imagery/slice';
import './style.css';
import { getImageNames, getSelectedImages } from '~/features/Imagery/selector';

const CameraPanel = ({ selectedImages, imgNames, dispatch }) => {
  const handleLoadImageFromNuc = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/get_image_list');
      const { result } = await res.json();

      if (result.length === 0) {
        dispatch(showError('There is no Detected Image found in the Server'));
        return;
      }

      dispatch(setImageNames(result));
    } catch (e) {
      console.log(e?.message);
      dispatch(showError('Failed to load images from server'));
    }
  };

  const handleImageSelect = (imgName) => {
    dispatch(toggleImageSelection(imgName));
  };

  const handleSelectAll = () => {
    if (selectedImages.length === imgNames.length) {
      dispatch(clearImageSelection());
    } else {
      dispatch(selectAllImages());
    }
  };

  const formatFileName = (name) => {
    const split = name.split('_');
    return `Home: ${split[3]}, ${split[4]}`;
  };

  const handleUseSelectedImages = () => {
    // Implement what happens when user clicks "Use Selected Images"
    console.log('Using selected images:', selectedImages);
    // dispatch(openOnLoadImage(selectedImages)); // Uncomment when ready to implement
  };

  return (
    <Box
      style={{
        margin: 10,
        gap: 20,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'auto',
      }}
    >
      <Box
        display='flex'
        justifyContent='space-between'
        alignItems='center'
        mb={2}
        p={1}
        // bgcolor='#f5f5f5'
        borderRadius={4}
      >
        <div>
          <Button
            variant='contained'
            color='primary'
            onClick={handleLoadImageFromNuc}
            style={{ marginRight: 8 }}
          >
            Load Images
          </Button>
          {imgNames.length > 0 && (
            <Button variant='outlined' onClick={handleSelectAll}>
              {selectedImages.length === imgNames.length
                ? 'Deselect All'
                : 'Select All'}
            </Button>
          )}
        </div>

        {selectedImages.length > 0 && (
          <div>
            <Typography
              variant='body2'
              style={{ marginRight: 8, display: 'inline-block' }}
            >
              {selectedImages.length} selected
            </Typography>
            <Button
              variant='contained'
              color='secondary'
              onClick={handleUseSelectedImages}
            >
              Use Selected Images
            </Button>
          </div>
        )}
      </Box>

      {selectedImages.length === 1 && (
        <div className='img-info'>
          <Typography variant='body2' noWrap>
            Image
          </Typography>
        </div>
      )}
      <Box className='container'>
        {imgNames.length > 0 &&
          imgNames.map((imgName, i) => (
            <div
              key={`img-card-${i}`}
              className={`img-card ${selectedImages.includes(imgName) ? 'selected' : ''}`}
              onClick={() => handleImageSelect(imgName)}
            >
              <img
                className='img-style'
                src={`http://127.0.0.1:8000/get_image/${imgName}`}
                alt={`Image ${i + 1}`}
              />
              <div className='img-info'>
                <Typography variant='body2' noWrap>
                  {formatFileName(imgName)}
                </Typography>
              </div>
            </div>
          ))}
      </Box>
      {imgNames.length === 0 && (
        <Box textAlign='center' p={3}>
          <Typography variant='body1' color='textSecondary'>
            No images available. Click "Load Images" to fetch from server.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default connect(
  (state) => ({
    imgNames: getImageNames(state),
    selectedImages: getSelectedImages(state),
  }),
  (dispatch) => ({ dispatch })
)(CameraPanel);

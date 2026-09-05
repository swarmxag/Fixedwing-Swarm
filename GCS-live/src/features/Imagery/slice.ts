/**
 * @file Slice of the state object that handles the tabular datasets loaded
 * by the user.
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

type TypeImagery = {
  imgNames: string[];
  selectedImages: string[];
};

const initialState: TypeImagery = {
  imgNames: [],
  selectedImages: [],
};

const { actions, reducer } = createSlice({
  name: 'imagery',
  initialState,
  reducers: {
    setImageNames: (state, action: PayloadAction<string[]>) => {
      state.imgNames = action.payload;
    },
    toggleImageSelection: (state, action: PayloadAction<string>) => {
      const imgName = action.payload;
      const index = state.selectedImages.indexOf(imgName);

      if (index === -1) {
        state.selectedImages.push(imgName);
      } else {
        state.selectedImages.splice(index, 1);
      }
    },
    selectAllImages: (state) => {
      state.selectedImages = [...state.imgNames];
    },
    clearImageSelection: (state) => {
      state.selectedImages = [];
    },
    setSelectedImages: (state, action: PayloadAction<string[]>) => {
      state.selectedImages = action.payload;
    },
  },
});

export const {
  setImageNames,
  toggleImageSelection,
  selectAllImages,
  clearImageSelection,
  setSelectedImages,
} = actions;

export default reducer;

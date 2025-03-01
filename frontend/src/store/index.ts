import { configureStore } from '@reduxjs/toolkit';
import { combineReducers } from 'redux';
import simulationReducer from './simulationSlice';
import activityLogReducer from './activityLogSlice';
import charactersReducer from './charactersSlice';
import portfolioReducer from './portfolioSlice';

const rootReducer = combineReducers({
  simulation: simulationReducer,
  activityLog: activityLogReducer,
  characters: charactersReducer,
  portfolio: portfolioReducer,
});

export const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
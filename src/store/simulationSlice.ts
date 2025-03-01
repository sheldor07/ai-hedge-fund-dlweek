import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface PerformanceMetric {
  timestamp: number;
  value: number;
  type: 'return' | 'alpha' | 'sharpe' | 'drawdown';
}

export interface MarketEvent {
  id: string;
  timestamp: number;
  type: string;
  description: string;
  impact: 'positive' | 'negative' | 'neutral';
  magnitude: number;
}

interface SimulationState {
  isRunning: boolean;
  speed: number;
  dayNightCycle: number; // 0-1 representing time of day
  performanceMetrics: {
    return: PerformanceMetric[];
    alpha: PerformanceMetric[];
    sharpe: PerformanceMetric[];
    drawdown: PerformanceMetric[];
  };
  currentMarketEvents: MarketEvent[];
  simulationTime: number; // in milliseconds
  focusedEntity: { type: 'character' | 'room' | null; id: string | null };
  currentView: 'office' | 'knowledgeBase' | 'portfolio';
  selectedCompany: string | null;
}

const initialState: SimulationState = {
  isRunning: false,
  speed: 1,
  dayNightCycle: 0.5,
  performanceMetrics: {
    return: [],
    alpha: [],
    sharpe: [],
    drawdown: [],
  },
  currentMarketEvents: [],
  simulationTime: 0,
  focusedEntity: { type: null, id: null },
  currentView: 'office',
  selectedCompany: null,
};

export const simulationSlice = createSlice({
  name: 'simulation',
  initialState,
  reducers: {
    startSimulation: (state) => {
      state.isRunning = true;
    },
    pauseSimulation: (state) => {
      state.isRunning = false;
    },
    setSimulationSpeed: (state, action: PayloadAction<number>) => {
      state.speed = action.payload;
    },
    updateDayNightCycle: (state, action: PayloadAction<number>) => {
      state.dayNightCycle = action.payload;
    },
    addPerformanceMetric: (state, action: PayloadAction<PerformanceMetric>) => {
      const { type, ...metricData } = action.payload;
      state.performanceMetrics[type].push({ ...metricData, type });
    },
    addMarketEvent: (state, action: PayloadAction<MarketEvent>) => {
      state.currentMarketEvents.push(action.payload);
    },
    removeMarketEvent: (state, action: PayloadAction<string>) => {
      state.currentMarketEvents = state.currentMarketEvents.filter(
        (event) => event.id !== action.payload
      );
    },
    updateSimulationTime: (state, action: PayloadAction<number>) => {
      state.simulationTime = action.payload;
    },
    setFocusedEntity: (
      state,
      action: PayloadAction<{ type: 'character' | 'room' | null; id: string | null }>
    ) => {
      state.focusedEntity = action.payload;
    },
    setCurrentView: (
      state,
      action: PayloadAction<'office' | 'knowledgeBase' | 'portfolio'>
    ) => {
      state.currentView = action.payload;
    },
    setSelectedCompany: (
      state,
      action: PayloadAction<string | null>
    ) => {
      state.selectedCompany = action.payload;
    },
  },
});

export const {
  startSimulation,
  pauseSimulation,
  setSimulationSpeed,
  updateDayNightCycle,
  addPerformanceMetric,
  addMarketEvent,
  removeMarketEvent,
  updateSimulationTime,
  setFocusedEntity,
  setCurrentView,
  setSelectedCompany,
} = simulationSlice.actions;

export default simulationSlice.reducer;
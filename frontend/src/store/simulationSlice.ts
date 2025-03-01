import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { CharacterEvent, DailySchedulePeriod, TimeOfDayPeriod, DayType } from '../models/types';

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

// Schedule for the typical workday
export const DAILY_SCHEDULE: DailySchedulePeriod[] = [
  {
    periodType: 'MORNING_BRIEFING',
    startHour: 9,
    startMinute: 0,
    endHour: 9,
    endMinute: 30,
    description: 'Morning Briefing'
  },
  {
    periodType: 'ANALYSIS_PHASE',
    startHour: 9,
    startMinute: 30,
    endHour: 12,
    endMinute: 0,
    description: 'Analysis Phase'
  },
  {
    periodType: 'LUNCH_BREAK',
    startHour: 12,
    startMinute: 0,
    endHour: 13,
    endMinute: 0,
    description: 'Lunch Break'
  },
  {
    periodType: 'STRATEGY_MEETING',
    startHour: 13,
    startMinute: 0,
    endHour: 14,
    endMinute: 0,
    description: 'Strategy Meeting'
  },
  {
    periodType: 'TRADE_EXECUTION',
    startHour: 14,
    startMinute: 0,
    endHour: 15,
    endMinute: 30,
    description: 'Trade Execution'
  },
  {
    periodType: 'END_OF_DAY_REVIEW',
    startHour: 15,
    startMinute: 30,
    endHour: 17,
    endMinute: 0,
    description: 'End of Day Review'
  },
  {
    periodType: 'AFTER_HOURS',
    startHour: 17,
    startMinute: 0,
    endHour: 9,
    endMinute: 0,
    description: 'After Hours'
  }
];

interface SimulationState {
  // Onboarding state
  onboardingComplete: boolean;
  investmentAmount: number;
  
  // Running state
  isRunning: boolean;
  speed: number;
  speedOptions: number[]; // Available speed multipliers
  simulationStartDate: Date; // Start date of the simulation (March 1, 2023)
  simulationEndDate: Date; // End date of the simulation (March 1, 2024)
  currentDate: Date; // Current date in the simulation
  dayNightCycle: number; // 0-1 representing time of day
  currentTimeOfDay: TimeOfDayPeriod; // Current period in the daily schedule
  dayType: DayType; // Weekday or weekend
  performanceMetrics: {
    return: PerformanceMetric[];
    alpha: PerformanceMetric[];
    sharpe: PerformanceMetric[];
    drawdown: PerformanceMetric[];
  };
  currentMarketEvents: MarketEvent[];
  simulationTime: number; // in milliseconds
  pendingCharacterEvents: CharacterEvent[]; // Events scheduled but not yet executed
  activeCharacterEvents: CharacterEvent[]; // Events currently in progress
  completedCharacterEvents: CharacterEvent[]; // Events that have been completed
  focusedEntity: { type: 'character' | 'room' | null; id: string | null };
  currentView: 'office' | 'knowledgeBase' | 'portfolio';
  selectedCompany: string | null;
  
  // Tutorial state
  tutorialComplete: boolean;
  currentTutorialStep: number;
}

const initialState: SimulationState = {
  // Onboarding state
  onboardingComplete: false,
  investmentAmount: 1000000,
  
  // Running state
  isRunning: false,
  speed: 1,
  speedOptions: [1, 2, 5, 10, 50],
  simulationStartDate: new Date(2023, 2, 1, 9, 0, 0), // March 1, 2023, 9:00 AM
  simulationEndDate: new Date(2024, 2, 1, 17, 0, 0), // March 1, 2024, 5:00 PM
  currentDate: new Date(2023, 2, 1, 9, 0, 0), // Start with March 1, 2023, 9:00 AM
  dayNightCycle: 0.5,
  currentTimeOfDay: 'MORNING_BRIEFING',
  dayType: 'WEEKDAY',
  performanceMetrics: {
    return: [],
    alpha: [],
    sharpe: [],
    drawdown: [],
  },
  currentMarketEvents: [],
  simulationTime: 0,
  pendingCharacterEvents: [],
  activeCharacterEvents: [],
  completedCharacterEvents: [],
  focusedEntity: { type: null, id: null },
  currentView: 'office',
  selectedCompany: null,
  
  // Tutorial state
  tutorialComplete: false,
  currentTutorialStep: 0,
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
    updateCurrentDate: (state, action: PayloadAction<Date>) => {
      state.currentDate = action.payload;
      
      // Update day type (weekday or weekend)
      const day = action.payload.getDay();
      state.dayType = (day === 0 || day === 6) ? 'WEEKEND' : 'WEEKDAY';
      
      // Calculate time of day period
      const hours = action.payload.getHours();
      const minutes = action.payload.getMinutes();
      const timeInMinutes = hours * 60 + minutes;
      
      // Find the current period in the daily schedule
      let currentPeriod: TimeOfDayPeriod = 'AFTER_HOURS';
      for (const period of DAILY_SCHEDULE) {
        const startTimeInMinutes = period.startHour * 60 + period.startMinute;
        const endTimeInMinutes = period.endHour * 60 + period.endMinute;
        
        // Handle the special case for AFTER_HOURS which wraps around midnight
        if (period.periodType === 'AFTER_HOURS') {
          if (timeInMinutes >= startTimeInMinutes || timeInMinutes < endTimeInMinutes) {
            currentPeriod = period.periodType;
            break;
          }
        } else if (timeInMinutes >= startTimeInMinutes && timeInMinutes < endTimeInMinutes) {
          currentPeriod = period.periodType;
          break;
        }
      }
      
      state.currentTimeOfDay = currentPeriod;
    },
    addCharacterEvent: (state, action: PayloadAction<CharacterEvent>) => {
      // Add event to pending queue, sorted by timestamp and priority
      state.pendingCharacterEvents.push(action.payload);
      state.pendingCharacterEvents.sort((a, b) => {
        if (a.timestamp.getTime() !== b.timestamp.getTime()) {
          return a.timestamp.getTime() - b.timestamp.getTime();
        }
        return b.priority - a.priority; // Higher priority comes first if timestamps are equal
      });
    },
    activateCharacterEvent: (state, action: PayloadAction<string>) => {
      const eventIndex = state.pendingCharacterEvents.findIndex(e => e.id === action.payload);
      if (eventIndex !== -1) {
        const event = state.pendingCharacterEvents[eventIndex];
        state.activeCharacterEvents.push(event);
        state.pendingCharacterEvents.splice(eventIndex, 1);
      }
    },
    completeCharacterEvent: (state, action: PayloadAction<string>) => {
      const eventIndex = state.activeCharacterEvents.findIndex(e => e.id === action.payload);
      if (eventIndex !== -1) {
        const event = { ...state.activeCharacterEvents[eventIndex], completed: true };
        state.completedCharacterEvents.push(event);
        state.activeCharacterEvents.splice(eventIndex, 1);
        
        // Limit the size of completed events history
        if (state.completedCharacterEvents.length > 1000) {
          state.completedCharacterEvents = state.completedCharacterEvents.slice(-1000);
        }
      }
    },
    generateDailyEvents: (state, action: PayloadAction<Date>) => {
      // This reducer is a placeholder for the event generation logic
      // The actual implementation will be in the useSimulationEngine hook
    },
    fastForwardToNextDay: (state) => {
      // Move to the next day at 9:00 AM
      const nextDay = new Date(state.currentDate);
      nextDay.setDate(nextDay.getDate() + 1);
      nextDay.setHours(9, 0, 0, 0);
      state.currentDate = nextDay;
      state.currentTimeOfDay = 'MORNING_BRIEFING';
      
      // Update day type
      const day = nextDay.getDay();
      state.dayType = (day === 0 || day === 6) ? 'WEEKEND' : 'WEEKDAY';
      
      // Clear active events
      state.activeCharacterEvents = [];
    },
    fastForwardToNextWeekday: (state) => {
      // Move to the next weekday at 9:00 AM
      const nextDay = new Date(state.currentDate);
      do {
        nextDay.setDate(nextDay.getDate() + 1);
      } while (nextDay.getDay() === 0 || nextDay.getDay() === 6); // Skip weekends
      
      nextDay.setHours(9, 0, 0, 0);
      state.currentDate = nextDay;
      state.currentTimeOfDay = 'MORNING_BRIEFING';
      state.dayType = 'WEEKDAY';
      
      // Clear active events
      state.activeCharacterEvents = [];
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
    
    // Onboarding actions
    setInvestmentAmount: (state, action: PayloadAction<number>) => {
      state.investmentAmount = action.payload;
    },
    setSimulationPeriod: (state, action: PayloadAction<{ startDate: Date, endDate: Date }>) => {
      state.simulationStartDate = action.payload.startDate;
      state.simulationEndDate = action.payload.endDate;
      state.currentDate = new Date(action.payload.startDate);
    },
    completeOnboarding: (state) => {
      state.onboardingComplete = true;
    },
    
    // Tutorial actions
    setTutorialStep: (state, action: PayloadAction<number>) => {
      state.currentTutorialStep = action.payload;
    },
    completeTutorial: (state) => {
      state.tutorialComplete = true;
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
  updateCurrentDate,
  addCharacterEvent,
  activateCharacterEvent,
  completeCharacterEvent,
  generateDailyEvents,
  fastForwardToNextDay,
  fastForwardToNextWeekday,
  setFocusedEntity,
  setCurrentView,
  setSelectedCompany,
  
  // New actions
  setInvestmentAmount,
  setSimulationPeriod,
  completeOnboarding,
  setTutorialStep,
  completeTutorial,
} = simulationSlice.actions;

export default simulationSlice.reducer;
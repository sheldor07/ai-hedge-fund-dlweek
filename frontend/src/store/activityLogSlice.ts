import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ActivityLogEntry {
  id: string;
  timestamp: number;
  characterId: string;
  characterType: 'analyst' | 'quant' | 'executive' | 'riskManager';
  roomId: string;
  actionType: 'movement' | 'analysis' | 'decision' | 'communication' | 'trading';
  description: string;
  details?: any;
}

interface ActivityLogState {
  entries: ActivityLogEntry[];
  filter: {
    characterType: ('analyst' | 'quant' | 'executive' | 'riskManager')[] | null;
    roomId: string | null;
    actionType: ('movement' | 'analysis' | 'decision' | 'communication' | 'trading')[] | null;
  };
  autoScroll: boolean;
  showDetailed: boolean;
  searchQuery: string;
}

const initialState: ActivityLogState = {
  entries: [],
  filter: {
    characterType: null,
    roomId: null,
    actionType: null,
  },
  autoScroll: true,
  showDetailed: false,
  searchQuery: '',
};

export const activityLogSlice = createSlice({
  name: 'activityLog',
  initialState,
  reducers: {
    addLogEntry: (state, action: PayloadAction<ActivityLogEntry>) => {
      state.entries.push(action.payload);
      // Keep log size manageable by removing old entries if needed
      if (state.entries.length > 1000) {
        state.entries = state.entries.slice(-1000);
      }
    },
    setCharacterTypeFilter: (
      state,
      action: PayloadAction<('analyst' | 'quant' | 'executive' | 'riskManager')[] | null>
    ) => {
      state.filter.characterType = action.payload;
    },
    setRoomFilter: (state, action: PayloadAction<string | null>) => {
      state.filter.roomId = action.payload;
    },
    setActionTypeFilter: (
      state,
      action: PayloadAction<('movement' | 'analysis' | 'decision' | 'communication' | 'trading')[] | null>
    ) => {
      state.filter.actionType = action.payload;
    },
    clearFilters: (state) => {
      state.filter = {
        characterType: null,
        roomId: null,
        actionType: null,
      };
    },
    setAutoScroll: (state, action: PayloadAction<boolean>) => {
      state.autoScroll = action.payload;
    },
    setShowDetailed: (state, action: PayloadAction<boolean>) => {
      state.showDetailed = action.payload;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    clearLog: (state) => {
      state.entries = [];
    },
  },
});

export const {
  addLogEntry,
  setCharacterTypeFilter,
  setRoomFilter,
  setActionTypeFilter,
  clearFilters,
  setAutoScroll,
  setShowDetailed,
  setSearchQuery,
  clearLog,
} = activityLogSlice.actions;

export default activityLogSlice.reducer;
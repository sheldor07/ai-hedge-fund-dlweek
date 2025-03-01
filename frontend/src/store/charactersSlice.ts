import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Position {
  x: number;
  y: number;
  z: number;
}

export interface Target {
  position: Position;
  roomId?: string;
  characterId?: string;
}

export interface Character {
  id: string;
  name: string;
  type: 'analyst' | 'quant' | 'executive' | 'riskManager';
  position: Position;
  targetPosition: Target | null;
  rotation: number;
  currentRoom: string;
  state: 'idle' | 'walking' | 'working' | 'talking';
  currentTask: string | null;
  conversations: Array<{
    withCharacterId: string;
    content: string;
    timestamp: number;
  }>;
  skills: {
    analysis: number;
    decision: number;
    communication: number;
    risk: number;
  };
  activityHistory: string[];
}

interface CharactersState {
  characters: Character[];
}

const initialState: CharactersState = {
  characters: [],
};

export const charactersSlice = createSlice({
  name: 'characters',
  initialState,
  reducers: {
    addCharacter: (state, action: PayloadAction<Character>) => {
      state.characters.push(action.payload);
    },
    updateCharacterPosition: (
      state,
      action: PayloadAction<{ id: string; position: Position }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.position = action.payload.position;
      }
    },
    setCharacterTarget: (
      state,
      action: PayloadAction<{ id: string; target: Target | null }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.targetPosition = action.payload.target;
      }
    },
    updateCharacterRoom: (
      state,
      action: PayloadAction<{ id: string; roomId: string }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.currentRoom = action.payload.roomId;
      }
    },
    updateCharacterState: (
      state,
      action: PayloadAction<{
        id: string;
        state: 'idle' | 'walking' | 'working' | 'talking';
      }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.state = action.payload.state;
      }
    },
    updateCharacterTask: (
      state,
      action: PayloadAction<{ id: string; task: string | null }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.currentTask = action.payload.task;
      }
    },
    addConversation: (
      state,
      action: PayloadAction<{
        id: string;
        withCharacterId: string;
        content: string;
        timestamp: number;
      }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.conversations.push({
          withCharacterId: action.payload.withCharacterId,
          content: action.payload.content,
          timestamp: action.payload.timestamp,
        });
      }
    },
    addActivityToHistory: (
      state,
      action: PayloadAction<{ id: string; activity: string }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.activityHistory.push(action.payload.activity);
        // Keep history size manageable
        if (character.activityHistory.length > 50) {
          character.activityHistory = character.activityHistory.slice(-50);
        }
      }
    },
    updateCharacterRotation: (
      state,
      action: PayloadAction<{ id: string; rotation: number }>
    ) => {
      const character = state.characters.find((c) => c.id === action.payload.id);
      if (character) {
        character.rotation = action.payload.rotation;
      }
    },
  },
});

export const {
  addCharacter,
  updateCharacterPosition,
  setCharacterTarget,
  updateCharacterRoom,
  updateCharacterState,
  updateCharacterTask,
  addConversation,
  addActivityToHistory,
  updateCharacterRotation,
} = charactersSlice.actions;

export default charactersSlice.reducer;
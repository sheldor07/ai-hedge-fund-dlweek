// Room types
export type RoomType = 
  | 'fundamentalAnalysis' 
  | 'technicalAnalysis' 
  | 'executiveSuite' 
  | 'tradingFloor';

// Character types
export type CharacterType = 
  | 'analyst' 
  | 'quant' 
  | 'executive' 
  | 'riskManager';

// Activity types
export type ActivityType = 
  | 'movement' 
  | 'analysis' 
  | 'decision' 
  | 'communication' 
  | 'trading';

// Character states
export type CharacterState = 
  | 'idle' 
  | 'walking' 
  | 'working' 
  | 'talking';

// Room interfaces
export interface Room {
  id: string;
  type: RoomType;
  name: string;
  position: {
    x: number;
    y: number;
    z: number;
  };
  size: {
    width: number;
    height: number;
    depth: number;
  };
  assets: RoomAsset[];
  characters: string[]; // IDs of characters currently in the room
}

export interface RoomAsset {
  id: string;
  type: 'computer' | 'desk' | 'chair' | 'screen' | 'whiteboard' | 'conferenceTable';
  position: {
    x: number;
    y: number;
    z: number;
  };
  rotation: {
    x: number;
    y: number;
    z: number;
  };
  scale: {
    x: number;
    y: number;
    z: number;
  };
  interactionPoints?: {
    x: number;
    y: number;
    z: number;
  }[];
}

// Performance metric types
export type MetricType = 'return' | 'alpha' | 'sharpe' | 'drawdown';

export interface Metric {
  type: MetricType;
  value: number;
  timestamp: number;
}
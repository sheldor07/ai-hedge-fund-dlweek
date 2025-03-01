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

// Company types for knowledge base
export interface CompanyNews {
  id: string;
  date: string;
  headline: string;
  summary: string;
  impact: 'positive' | 'negative' | 'neutral';
}

export interface CompanyFinancials {
  revenue: string;
  profit: string;
  growthRate: string;
  peRatio: string;
  marketCap: string;
  dividendYield: string;
}

export interface CompanyDocument {
  id: string;
  title: string;
  type: 'pdf' | 'spreadsheet' | 'presentation';
  description: string;
}

export interface Company {
  id: string;
  ticker: string;
  name: string;
  logo: string;
  description: string;
  sector: string;
  industry: string;
  website: string;
  financials: CompanyFinancials;
  news: CompanyNews[];
  documents: CompanyDocument[];
}
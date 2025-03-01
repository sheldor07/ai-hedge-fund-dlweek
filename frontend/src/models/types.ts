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

// Event types for the Character Event System
export type EventType = 
  | 'MOVE' 
  | 'ANALYZE' 
  | 'DISCUSS' 
  | 'DECIDE' 
  | 'REACT';

// Simulation event types
export type SimulationEventType = 
  | 'PLANNING' 
  | 'ANALYSIS' 
  | 'MEETING' 
  | 'DECISION' 
  | 'EXECUTION';

// Trading actions
export type TradeAction = 'BUY' | 'SELL' | 'HOLD';

// Order status
export type OrderStatus = 'PENDING' | 'EXECUTED' | 'CANCELLED';

// Time of day periods for the daily schedule
export type TimeOfDayPeriod = 
  | 'MORNING_BRIEFING'
  | 'ANALYSIS_PHASE'
  | 'LUNCH_BREAK'
  | 'STRATEGY_MEETING'
  | 'TRADE_EXECUTION'
  | 'END_OF_DAY_REVIEW'
  | 'AFTER_HOURS';

// Day type for weekend handling
export type DayType = 
  | 'WEEKDAY' 
  | 'WEEKEND';

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

// Character Event System
export interface CharacterEvent {
  id: string;
  timestamp: Date;
  characterIds: string[];
  originRoom: string;
  destinationRoom?: string; // Optional for non-movement events
  eventType: EventType;
  message: string;
  duration: number; // in milliseconds
  relatedStock?: string; // AMZN, NVDA, MU, WMT, DIS
  priority: number; // For conflict resolution
  completed: boolean;
}

// Daily Schedule Period 
export interface DailySchedulePeriod {
  periodType: TimeOfDayPeriod;
  startHour: number;
  startMinute: number;
  endHour: number;
  endMinute: number;
  description: string;
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

// Enhanced simulation event system
export interface Event {
  id: string;
  day: number; // Day count from simulation start
  date: string; // YYYY-MM-DD format
  time: string; // HH:MM format
  type: SimulationEventType;
  characters: string[]; // Character IDs involved
  location: string; // Room ID where event occurs
  description: string;
  dialogues: Dialogue[];
  duration: number; // Minutes
  relatedStock?: string; // Stock ticker (optional)
  tradingDecision?: TradingDecision; // Decision details (optional)
  completed: boolean;
  priority: number; // For scheduling conflicts
}

export interface Dialogue {
  characterId: string;
  message: string;
  timing: number; // Seconds after event start
}

export interface TradingDecision {
  stock: string; // Ticker symbol
  action: TradeAction;
  quantity: number; // Number of shares
  price: number; // Price per share
  rationale: string; // Reasoning
  confidence: number; // 0-100%
  analysisType: 'TECHNICAL' | 'FUNDAMENTAL';
}

// Order book system
export interface OrderBook {
  orders: Order[];
  historicalOrders: Order[];
}

export interface Order {
  id: string;
  date: string; // YYYY-MM-DD
  time: string; // HH:MM:SS
  stock: string; // Ticker symbol
  action: TradeAction;
  quantity: number; // Number of shares
  price: number; // Per share
  status: OrderStatus;
  executedBy: string; // Character ID
  totalValue: number; // quantity * price
  fees: number; // Transaction costs
  eventId: string; // Reference to generating event
}

// Portfolio system
export interface Portfolio {
  cash: number; // Available cash
  totalValue: number; // Cash + holdings value
  holdings: Holding[];
  performanceHistory: DailyPerformance[];
}

export interface Holding {
  stock: string; // Ticker symbol
  quantity: number; // Shares owned
  averagePurchasePrice: number; // Cost basis
  currentPrice: number; // Current market price
  currentValue: number; // quantity * currentPrice
  unrealizedPnL: number; // Profit/loss in dollars
  unrealizedPnLPercent: number; // Profit/loss percentage
  allocation: number; // Percentage of portfolio
}

export interface DailyPerformance {
  date: string; // YYYY-MM-DD
  totalValue: number; // Portfolio value
  dailyChange: number; // Dollar change
  dailyChangePercent: number; // Percentage change
  cash: number; // Cash amount
  holdings: Holding[]; // Copy of holdings for this day
}
import { 
  Event, 
  Dialogue, 
  TradingDecision, 
  SimulationEventType,
  TradeAction
} from '../models/types';
import { DAILY_SCHEDULE } from '../store/simulationSlice';
import { MarketEvent } from '../store/simulationSlice';
import { ActivityLogEntry } from '../store/activityLogSlice';

// Array of stocks that the simulation will track
export const TRACKED_STOCKS = ['AMZN', 'NVDA', 'MU', 'WMT', 'DIS'];

// Map of room IDs to names
export const ROOM_MAP = {
  'room-0': 'Fundamental Analysis Room',
  'room-1': 'Technical Analysis Room',
  'room-2': 'CEO Office',
  'room-3': 'Decision Room',
};

/**
 * Legacy interface for backward compatibility
 */
export interface SimulatedEvent {
  timestamp: string;
  type: string;
  ticker?: string;
  message: string;
  direction?: 'up' | 'down';
  percent?: number;
  rating?: string;
  target?: number;
  action?: 'BUY' | 'SELL';
  quantity?: number;
  price?: number;
  indicator?: string;
  actual?: number;
  forecast?: number;
  companies?: string[];
  index?: string;
  points?: number;
  sector?: string;
}

export interface SimulatedEventsData {
  events: SimulatedEvent[];
}

// Character dialogue templates for different event types
const DIALOGUE_TEMPLATES = {
  PLANNING: {
    CEO: [
      "Let's focus on {stock} today. I want a thorough analysis by noon.",
      "I need everyone to analyze {stock}. Their earnings report is coming up.",
      "The market's been volatile. Let's review our {stock} position today.",
      "We should consider adjusting our {stock} exposure. What's the outlook?",
      "I want a detailed analysis of {stock}'s recent price movements."
    ],
    ANALYST: [
      "I'll look into {stock}'s latest financials and prepare a report.",
      "I'll check analyst sentiment on {stock} and recent news coverage.",
      "I can research {stock}'s competitive position in the market.",
      "I'll analyze {stock}'s valuation metrics compared to peers.",
      "I'll examine {stock}'s recent SEC filings for any red flags."
    ],
    QUANT: [
      "I'll run our models on {stock} and see what the algorithms predict.",
      "I can analyze {stock}'s price patterns and momentum indicators.",
      "I'll check {stock}'s correlation with sector performance.",
      "Let me run a volatility analysis on {stock} trading patterns.",
      "I'll look at {stock}'s technical indicators for entry/exit signals."
    ]
  },
  ANALYSIS: {
    ANALYST: [
      "Looking at {stock}'s P/E ratio of {num}, it's {direction} the sector average.",
      "The debt-to-equity ratio for {stock} is concerning at {num}.",
      "{stock}'s revenue growth is {direction} projections by {num}%.",
      "Management's guidance for {stock} suggests {direction} earnings expectations.",
      "{stock}'s cash position has {direction} to ${num} million this quarter."
    ],
    QUANT: [
      "My algorithm shows a {num}% probability of {stock} breaking resistance.",
      "The MACD indicator for {stock} shows a {direction} trend forming.",
      "RSI for {stock} is at {num}, indicating it's {direction}bought.",
      "Volume analysis shows {direction} accumulation pattern for {stock}.",
      "The Bollinger Bands for {stock} are tightening, suggesting a big move soon."
    ]
  },
  MEETING: {
    CEO: [
      "Let's discuss what we've found about {stock}. What's your analysis?",
      "Give me your recommendations on {stock}. Should we adjust our position?",
      "I've reviewed the initial reports on {stock}. Let's dig deeper.",
      "The market is reacting to {stock}'s news. What's our position?",
      "We need to decide on {stock} today. What's the consensus?"
    ],
    ANALYST: [
      "My fundamental analysis suggests {stock} is {direction}valued by {num}%.",
      "Based on the latest earnings data, {stock} should {direction} by Q{num}.",
      "{stock}'s management team has been {direction} in their execution.",
      "Competitors are gaining ground on {stock} in the {num} key markets.",
      "Regulatory risks for {stock} have {direction} in the past quarter."
    ],
    QUANT: [
      "My models indicate a {num}% probability of {stock} trending {direction}.",
      "Technical analysis shows {stock} is approaching a {direction} breakout.",
      "Volatility metrics for {stock} suggest hedging with a {num}% stop-loss.",
      "The mean reversion algorithm predicts {stock} will {direction} to ${num}.",
      "Sentiment analysis of {stock} is showing {direction} momentum."
    ]
  },
  DECISION: {
    CEO: [
      "Based on our analysis, I think we should {action} {stock}.",
      "The risk-reward ratio for {stock} suggests we should {action}.",
      "Let's {action} {stock} at the current price of ${num}.",
      "I'm authorizing a {action} order for {stock} at market price.",
      "Our position in {stock} should be {action} by {num}%."
    ],
    ANALYST: [
      "My recommendation is to {action} {stock} based on fundamentals.",
      "The valuation metrics suggest we should {action} {stock}.",
      "Given the company's outlook, I suggest we {action} {stock}.",
      "My analysis indicates we should {action} {stock} with a ${num} target.",
      "The risk analysis supports a decision to {action} {stock}."
    ],
    QUANT: [
      "The algorithm recommends we {action} {stock} at this level.",
      "Technical indicators strongly suggest we {action} {stock}.",
      "Our trading model signals a {action} for {stock} with {num}% confidence.",
      "The quantitative analysis supports a {action} decision on {stock}.",
      "Based on pattern recognition, we should {action} {stock}."
    ]
  },
  EXECUTION: {
    CEO: [
      "Execute a {action} order for {num} shares of {stock} at market price.",
      "Let's {action} {stock}: {num} shares at current market price.",
      "I'm approving the {action} order for {stock} as discussed.",
      "Execute the {action} strategy for {stock} we outlined.",
      "Proceed with the {action} order for {stock} at ${num} per share."
    ],
    QUANT: [
      "Executing {action} order for {stock}: {num} shares at market price.",
      "Order placed: {action} {num} shares of {stock} at ${price}.",
      "Transaction complete: {action} {stock} at ${price}, {num} shares.",
      "The {action} order for {stock} has been filled at ${price}.",
      "Successfully executed {action} for {stock}: {num} shares at ${price}."
    ]
  }
};

/**
 * Helper function to format date and time strings
 */
const formatDateTime = (date: Date): { dateStr: string, timeStr: string } => {
  const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const timeStr = `${hours}:${minutes}`;
  
  return { dateStr, timeStr };
};

/**
 * Generates a unique ID for events
 */
const generateId = (): string => {
  return `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Calculates the number of days between two dates
 */
const daysBetween = (startDate: Date, endDate: Date): number => {
  const oneDay = 24 * 60 * 60 * 1000; // hours*minutes*seconds*milliseconds
  return Math.round(Math.abs((startDate.getTime() - endDate.getTime()) / oneDay));
};

/**
 * Generates a random trading decision
 */
const generateTradingDecision = (
  stock: string, 
  action: TradeAction, 
  analysisType: 'TECHNICAL' | 'FUNDAMENTAL'
): TradingDecision => {
  // Generate random price between $50 and $800
  const price = Math.round((50 + Math.random() * 750) * 100) / 100;
  
  // Generate random quantity between 100 and 1000 shares
  const quantity = Math.round(100 + Math.random() * 900);
  
  // Generate random confidence between 60% and 95%
  const confidence = Math.round(60 + Math.random() * 35);
  
  // Generate rationale based on analysis type
  let rationale = '';
  if (analysisType === 'TECHNICAL') {
    const technicalReasons = [
      `${stock} is approaching a key support level at $${(price * 0.95).toFixed(2)}`,
      `${stock} has formed a bullish divergence pattern`,
      `${stock} is showing strong momentum on the RSI indicator`,
      `${stock} has broken through its 50-day moving average`,
      `${stock} is showing a cup and handle formation`
    ];
    rationale = technicalReasons[Math.floor(Math.random() * technicalReasons.length)];
  } else {
    const fundamentalReasons = [
      `${stock}'s P/E ratio indicates it's undervalued compared to peers`,
      `${stock}'s recent earnings growth suggests strong future performance`,
      `${stock} has increased its dividend by 15% year-over-year`,
      `${stock}'s management has announced a new product line`,
      `${stock} is expanding into new markets with significant growth potential`
    ];
    rationale = fundamentalReasons[Math.floor(Math.random() * fundamentalReasons.length)];
  }
  
  return {
    stock,
    action,
    quantity,
    price,
    rationale,
    confidence,
    analysisType
  };
};

/**
 * Generates events for a specific day
 */
export const generateEventsForDay = (
  day: number,
  date: Date,
  characters: { id: string, type: string, name: string }[]
): Event[] => {
  const events: Event[] = [];
  const { dateStr } = formatDateTime(date);
  const dayOfWeek = date.getDay();
  
  // Skip weekends
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    return events;
  }
  
  // Select a focus stock for the day
  const focusStock = TRACKED_STOCKS[Math.floor(Math.random() * TRACKED_STOCKS.length)];
  
  // Get CEO character
  const ceo = characters.find(c => c.type === 'executive') || { 
    id: 'ceo-1', 
    type: 'executive',
    name: 'CEO'
  };
  
  // Get a fundamental analyst
  const fundamentalAnalyst = characters.find(c => c.type === 'analyst') || {
    id: 'analyst-1',
    type: 'analyst',
    name: 'Fundamental Analyst'
  };
  
  // Get a quant analyst
  const quantAnalyst = characters.find(c => c.type === 'quant') || {
    id: 'quant-1',
    type: 'quant',
    name: 'Quant Analyst'
  };
  
  // Get a risk manager
  const riskManager = characters.find(c => c.type === 'riskManager') || {
    id: 'risk-1',
    type: 'riskManager',
    name: 'Risk Manager'
  };
  
  // Generate events for each period in the day
  DAILY_SCHEDULE.forEach(period => {
    // Skip after hours
    if (period.periodType === 'AFTER_HOURS') {
      return;
    }
    
    // For each period, create appropriate events
    const periodStartDate = new Date(date);
    periodStartDate.setHours(period.startHour, period.startMinute, 0, 0);
    
    const periodEndDate = new Date(date);
    periodEndDate.setHours(period.endHour, period.endMinute, 0, 0);
    
    // Calculate duration in minutes
    const durationMinutes = 
      (periodEndDate.getTime() - periodStartDate.getTime()) / (60 * 1000);
    
    // Get a random time within the period
    const randomMinutesOffset = Math.floor(Math.random() * (durationMinutes * 0.6));
    const eventDate = new Date(periodStartDate);
    eventDate.setMinutes(eventDate.getMinutes() + randomMinutesOffset);
    
    const { timeStr } = formatDateTime(eventDate);
    
    // Generate event based on period type
    switch (period.periodType) {
      case 'MORNING_BRIEFING': {
        // Morning planning event with CEO
        const planningEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: timeStr,
          type: 'PLANNING',
          characters: [ceo.id, fundamentalAnalyst.id, quantAnalyst.id, riskManager.id],
          location: 'room-2', // CEO Office
          description: `Morning planning meeting to discuss ${focusStock} analysis`,
          dialogues: [
            {
              characterId: ceo.id,
              message: DIALOGUE_TEMPLATES.PLANNING.CEO[Math.floor(Math.random() * DIALOGUE_TEMPLATES.PLANNING.CEO.length)]
                .replace('{stock}', focusStock),
              timing: 0
            },
            {
              characterId: fundamentalAnalyst.id,
              message: DIALOGUE_TEMPLATES.PLANNING.ANALYST[Math.floor(Math.random() * DIALOGUE_TEMPLATES.PLANNING.ANALYST.length)]
                .replace('{stock}', focusStock),
              timing: 10
            },
            {
              characterId: quantAnalyst.id,
              message: DIALOGUE_TEMPLATES.PLANNING.QUANT[Math.floor(Math.random() * DIALOGUE_TEMPLATES.PLANNING.QUANT.length)]
                .replace('{stock}', focusStock),
              timing: 20
            }
          ],
          duration: 30, // 30 minutes
          relatedStock: focusStock,
          completed: false,
          priority: 5
        };
        events.push(planningEvent);
        break;
      }
      
      case 'ANALYSIS_PHASE': {
        // Technical analysis event
        const technicalEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: timeStr,
          type: 'ANALYSIS',
          characters: [quantAnalyst.id],
          location: 'room-1', // Technical Analysis Room
          description: `Technical analysis of ${focusStock} price patterns`,
          dialogues: [
            {
              characterId: quantAnalyst.id,
              message: DIALOGUE_TEMPLATES.ANALYSIS.QUANT[Math.floor(Math.random() * DIALOGUE_TEMPLATES.ANALYSIS.QUANT.length)]
                .replace('{stock}', focusStock)
                .replace('{num}', (Math.floor(Math.random() * 85) + 15).toString())
                .replace('{direction}', Math.random() > 0.5 ? 'up' : 'down'),
              timing: 0
            }
          ],
          duration: 60, // 60 minutes
          relatedStock: focusStock,
          completed: false,
          priority: 3
        };
        events.push(technicalEvent);
        
        // Stagger fundamental analysis event
        const fundamentalDate = new Date(eventDate);
        fundamentalDate.setMinutes(fundamentalDate.getMinutes() + 45);
        const { timeStr: fundamentalTimeStr } = formatDateTime(fundamentalDate);
        
        // Fundamental analysis event
        const fundamentalEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: fundamentalTimeStr,
          type: 'ANALYSIS',
          characters: [fundamentalAnalyst.id],
          location: 'room-0', // Fundamental Analysis Room
          description: `Fundamental analysis of ${focusStock} financials`,
          dialogues: [
            {
              characterId: fundamentalAnalyst.id,
              message: DIALOGUE_TEMPLATES.ANALYSIS.ANALYST[Math.floor(Math.random() * DIALOGUE_TEMPLATES.ANALYSIS.ANALYST.length)]
                .replace('{stock}', focusStock)
                .replace('{num}', (Math.floor(Math.random() * 20) + 5).toString())
                .replace('{direction}', Math.random() > 0.5 ? 'above' : 'below'),
              timing: 0
            }
          ],
          duration: 75, // 75 minutes
          relatedStock: focusStock,
          completed: false,
          priority: 3
        };
        events.push(fundamentalEvent);
        break;
      }
      
      case 'LUNCH_BREAK': {
        // Lunch meeting with random characters
        const lunchEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: timeStr,
          type: 'MEETING',
          characters: [
            Math.random() > 0.5 ? ceo.id : riskManager.id, 
            Math.random() > 0.5 ? fundamentalAnalyst.id : quantAnalyst.id
          ],
          location: 'room-3', // Decision Room
          description: `Informal lunch discussion about ${focusStock}`,
          dialogues: [
            {
              characterId: Math.random() > 0.5 ? ceo.id : riskManager.id,
              message: `What's your take on ${focusStock}'s performance today?`,
              timing: 0
            },
            {
              characterId: Math.random() > 0.5 ? fundamentalAnalyst.id : quantAnalyst.id,
              message: `I'm seeing some interesting patterns in ${focusStock}'s trading volume.`,
              timing: 15
            }
          ],
          duration: 30, // 30 minutes
          relatedStock: focusStock,
          completed: false,
          priority: 2
        };
        events.push(lunchEvent);
        break;
      }
      
      case 'STRATEGY_MEETING': {
        // Strategy meeting with all characters
        const meetingEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: timeStr,
          type: 'MEETING',
          characters: [ceo.id, fundamentalAnalyst.id, quantAnalyst.id, riskManager.id],
          location: 'room-3', // Decision Room
          description: `Strategy meeting to discuss ${focusStock} position`,
          dialogues: [
            {
              characterId: ceo.id,
              message: DIALOGUE_TEMPLATES.MEETING.CEO[Math.floor(Math.random() * DIALOGUE_TEMPLATES.MEETING.CEO.length)]
                .replace('{stock}', focusStock),
              timing: 0
            },
            {
              characterId: fundamentalAnalyst.id,
              message: DIALOGUE_TEMPLATES.MEETING.ANALYST[Math.floor(Math.random() * DIALOGUE_TEMPLATES.MEETING.ANALYST.length)]
                .replace('{stock}', focusStock)
                .replace('{num}', (Math.floor(Math.random() * 4) + 1).toString())
                .replace('{direction}', Math.random() > 0.5 ? 'over' : 'under'),
              timing: 15
            },
            {
              characterId: quantAnalyst.id,
              message: DIALOGUE_TEMPLATES.MEETING.QUANT[Math.floor(Math.random() * DIALOGUE_TEMPLATES.MEETING.QUANT.length)]
                .replace('{stock}', focusStock)
                .replace('{num}', (Math.floor(Math.random() * 20) + 70).toString())
                .replace('{direction}', Math.random() > 0.5 ? 'upward' : 'downward'),
              timing: 30
            }
          ],
          duration: 60, // 60 minutes
          relatedStock: focusStock,
          completed: false,
          priority: 4
        };
        events.push(meetingEvent);
        break;
      }
      
      case 'TRADE_EXECUTION': {
        // Generate a trading decision
        const tradeAction: TradeAction = Math.random() > 0.6 ? 'BUY' : 'SELL';
        const analysisTechnique = Math.random() > 0.5 ? 'TECHNICAL' : 'FUNDAMENTAL';
        const tradingDecision = generateTradingDecision(
          focusStock, 
          tradeAction, 
          analysisTechnique
        );
        
        // Decision event
        const decisionEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: timeStr,
          type: 'DECISION',
          characters: [ceo.id, fundamentalAnalyst.id, quantAnalyst.id],
          location: 'room-2', // CEO Office
          description: `Decision on ${focusStock} trading position`,
          dialogues: [
            {
              characterId: ceo.id,
              message: DIALOGUE_TEMPLATES.DECISION.CEO[Math.floor(Math.random() * DIALOGUE_TEMPLATES.DECISION.CEO.length)]
                .replace('{stock}', focusStock)
                .replace('{action}', tradeAction.toLowerCase())
                .replace('{num}', Math.floor(tradingDecision.price).toString()),
              timing: 0
            },
            {
              characterId: analysisTechnique === 'FUNDAMENTAL' ? fundamentalAnalyst.id : quantAnalyst.id,
              message: analysisTechnique === 'FUNDAMENTAL' 
                ? DIALOGUE_TEMPLATES.DECISION.ANALYST[Math.floor(Math.random() * DIALOGUE_TEMPLATES.DECISION.ANALYST.length)]
                    .replace('{stock}', focusStock)
                    .replace('{action}', tradeAction.toLowerCase())
                    .replace('{num}', Math.floor(tradingDecision.price).toString())
                : DIALOGUE_TEMPLATES.DECISION.QUANT[Math.floor(Math.random() * DIALOGUE_TEMPLATES.DECISION.QUANT.length)]
                    .replace('{stock}', focusStock)
                    .replace('{action}', tradeAction.toLowerCase())
                    .replace('{num}', tradingDecision.confidence.toString()),
              timing: 15
            }
          ],
          duration: 30, // 30 minutes
          relatedStock: focusStock,
          tradingDecision,
          completed: false,
          priority: 5
        };
        events.push(decisionEvent);
        
        // Execution event (30 minutes later)
        const executionDate = new Date(eventDate);
        executionDate.setMinutes(executionDate.getMinutes() + 30);
        const { timeStr: executionTimeStr } = formatDateTime(executionDate);
        
        const executionEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: executionTimeStr,
          type: 'EXECUTION',
          characters: [ceo.id, quantAnalyst.id],
          location: 'room-3', // Decision Room
          description: `Execution of ${tradeAction} order for ${focusStock}`,
          dialogues: [
            {
              characterId: ceo.id,
              message: DIALOGUE_TEMPLATES.EXECUTION.CEO[Math.floor(Math.random() * DIALOGUE_TEMPLATES.EXECUTION.CEO.length)]
                .replace('{stock}', focusStock)
                .replace('{action}', tradeAction.toLowerCase())
                .replace('{num}', tradingDecision.quantity.toString())
                .replace('{price}', tradingDecision.price.toFixed(2)),
              timing: 0
            },
            {
              characterId: quantAnalyst.id,
              message: DIALOGUE_TEMPLATES.EXECUTION.QUANT[Math.floor(Math.random() * DIALOGUE_TEMPLATES.EXECUTION.QUANT.length)]
                .replace('{stock}', focusStock)
                .replace('{action}', tradeAction.toLowerCase())
                .replace('{num}', tradingDecision.quantity.toString())
                .replace('{price}', tradingDecision.price.toFixed(2)),
              timing: 15
            }
          ],
          duration: 30, // 30 minutes
          relatedStock: focusStock,
          tradingDecision,
          completed: false,
          priority: 5
        };
        events.push(executionEvent);
        break;
      }
      
      case 'END_OF_DAY_REVIEW': {
        // End of day review
        const reviewEvent: Event = {
          id: generateId(),
          day,
          date: dateStr,
          time: timeStr,
          type: 'MEETING',
          characters: [ceo.id, riskManager.id],
          location: 'room-2', // CEO Office
          description: `End of day review of portfolio performance`,
          dialogues: [
            {
              characterId: ceo.id,
              message: `How did our ${focusStock} trades perform today?`,
              timing: 0
            },
            {
              characterId: riskManager.id,
              message: `The ${focusStock} position ${Math.random() > 0.5 ? 'contributed positively' : 'slightly underperformed'} compared to the market.`,
              timing: 15
            }
          ],
          duration: 30, // 30 minutes
          completed: false,
          priority: 3
        };
        events.push(reviewEvent);
        break;
      }
    }
  });
  
  return events;
};

/**
 * Generates events for the specified timeframe
 */
export const generateEventsForTimeframe = (
  startDate: Date, 
  endDate: Date,
  characters: { id: string, type: string, name: string }[]
): Event[] => {
  const events: Event[] = [];
  const days = daysBetween(startDate, endDate);
  
  // Generate events for each day
  for (let i = 0; i < days; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(currentDate.getDate() + i);
    
    const dayEvents = generateEventsForDay(i, currentDate, characters);
    events.push(...dayEvents);
  }
  
  return events;
};

/**
 * Maps a stock ticker to the CEO's room
 */
export const getStockRoomAssignment = (ticker: string): string => {
  // We're using a fixed mapping here for simplicity
  return 'room-2'; // CEO Office
};

/**
 * Maps a simulated event from the pre-generated JSON to a MarketEvent object
 * (Legacy function for backward compatibility)
 */
export const mapToMarketEvent = (event: SimulatedEvent): MarketEvent => {
  // Define defaults for impact and magnitude based on event type
  let impact: 'positive' | 'negative' | 'neutral' = 'neutral';
  let magnitude = 0.2;

  // Determine impact based on event properties
  if (event.direction === 'up' || 
      (event.percent && event.percent > 0) ||
      event.type === 'M&A') {
    impact = 'positive';
    magnitude = event.percent ? event.percent / 10 : 0.2;
  } else if (event.direction === 'down' || 
            (event.percent && event.percent < 0)) {
    impact = 'negative';
    magnitude = event.percent ? Math.abs(event.percent) / 10 : 0.2;
  }

  // Special case for TRADE events - impact based on action
  if (event.type === 'TRADE') {
    impact = event.action === 'BUY' ? 'positive' : 'negative';
    magnitude = 0.1;
  }

  return {
    id: `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(event.timestamp).getTime(),
    type: event.type,
    description: event.message,
    impact,
    magnitude,
  };
};

/**
 * Maps a simulated event from the pre-generated JSON to an ActivityLogEntry
 * (Legacy function for backward compatibility)
 */
export const mapToActivityLogEntry = (event: SimulatedEvent): ActivityLogEntry => {
  // Determine action type based on event type
  let actionType: 'movement' | 'analysis' | 'decision' | 'communication' | 'trading' = 'communication';
  
  if (event.type === 'TRADE') {
    actionType = 'trading';
  } else if (event.type === 'ANALYST_RATING' || event.type === 'ECONOMIC_DATA') {
    actionType = 'analysis';
  } else if (event.type === 'PRICE_MOVEMENT' || event.type === 'MARKET_MOVEMENT') {
    actionType = 'decision';
  } else if (event.type === 'SECTOR_ROTATION') {
    actionType = 'movement';
  }

  let characterType: 'analyst' | 'quant' | 'executive' | 'riskManager' = 'analyst';
  
  // Determine character type based on event
  if (event.type === 'TRADE') {
    characterType = 'quant';
  } else if (event.type === 'ANALYST_RATING') {
    characterType = 'analyst';
  } else if (event.type === 'MARKET_MOVEMENT' || event.type === 'ECONOMIC_DATA') {
    characterType = 'executive';
  } else if (event.type === 'SECTOR_ROTATION' || event.type === 'PRICE_MOVEMENT') {
    characterType = 'riskManager';
  }

  return {
    id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(event.timestamp).getTime(),
    characterId: 'system-event',
    characterType,
    roomId: 'room-3',  // Trading floor
    actionType,
    description: event.message,
    details: {
      ticker: event.ticker,
      action: event.action,
      price: event.price,
      quantity: event.quantity,
      direction: event.direction,
      percent: event.percent,
      rating: event.rating,
      target: event.target,
      index: event.index,
      points: event.points,
      sector: event.sector,
      indicator: event.indicator,
      actual: event.actual,
      forecast: event.forecast,
    }
  };
};

/**
 * Converts an Event to an ActivityLogEntry
 */
export const eventToActivityLogEntry = (event: Event): ActivityLogEntry => {
  // Map event type to action type
  let actionType: 'movement' | 'analysis' | 'decision' | 'communication' | 'trading';
  
  switch (event.type) {
    case 'ANALYSIS':
      actionType = 'analysis';
      break;
    case 'DECISION':
      actionType = 'decision';
      break;
    case 'EXECUTION':
      actionType = 'trading';
      break;
    case 'MEETING':
    case 'PLANNING':
      actionType = 'communication';
      break;
    default:
      actionType = 'movement';
  }
  
  // Map room ID to character type
  let characterType: 'analyst' | 'quant' | 'executive' | 'riskManager';
  
  switch (event.location) {
    case 'room-0': // Fundamental Analysis
      characterType = 'analyst';
      break;
    case 'room-1': // Technical Analysis
      characterType = 'quant';
      break;
    case 'room-2': // CEO Office
      characterType = 'executive';
      break;
    default:
      characterType = 'riskManager';
  }
  
  // Build details object
  const details: any = { };
  
  if (event.relatedStock) {
    details.ticker = event.relatedStock;
  }
  
  if (event.tradingDecision) {
    details.action = event.tradingDecision.action;
    details.price = event.tradingDecision.price;
    details.quantity = event.tradingDecision.quantity;
    details.confidence = event.tradingDecision.confidence;
    details.rationale = event.tradingDecision.rationale;
  }
  
  return {
    id: `log-${event.id}`,
    timestamp: new Date(`${event.date}T${event.time}`).getTime(),
    characterId: event.characters[0],
    characterType,
    roomId: event.location,
    actionType,
    description: event.description,
    details
  };
};

/**
 * Loads the simulated events from the JSON file
 * (Legacy function for backward compatibility)
 */
export const loadSimulatedEvents = async (): Promise<SimulatedEventsData> => {
  try {
    const response = await fetch('/data/simulated_events.json');
    if (!response.ok) {
      throw new Error(`Failed to load simulated events: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error loading simulated events:', error);
    return { events: [] };
  }
};

/**
 * Filters events that should be active at the current simulation time
 */
export const getEventsForTimestamp = (
  events: Event[],
  currentDate: Date,
  timeWindow: number = 300000 // 5 minute window by default
): Event[] => {
  const currentTime = currentDate.getTime();
  const startTime = currentTime - timeWindow;
  const endTime = currentTime + timeWindow;
  
  return events.filter(event => {
    const eventTime = new Date(`${event.date}T${event.time}`).getTime();
    return eventTime >= startTime && eventTime <= endTime;
  });
};
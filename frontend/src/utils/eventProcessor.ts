import { 
  Event, 
  Order, 
  DailyPerformance, 
  TradeAction, 
  TradingDecision,
  OrderStatus
} from '../models/types';
import { createOrderFromEvent } from './tradingSystem';
import { store } from '../store';
import { 
  executeOrder, 
  addOrder, 
  updateStockPrices, 
  addDailyPerformance 
} from '../store/portfolioSlice';
import { addLogEntry } from '../store/activityLogSlice';
import { addMarketEvent, removeMarketEvent } from '../store/simulationSlice';

/**
 * Processes simulation events to create orders for execution
 * Focuses on EXECUTION events which should have a tradingDecision
 */
export const processEventsForOrders = (
  events: Event[], 
  executorId: string
): Order[] => {
  // Filter to only execution events with trading decisions
  const executionEvents = events.filter(event => 
    event.type === 'EXECUTION' && 
    event.tradingDecision && 
    !event.completed
  );
  
  // Create orders from these events
  const orders: Order[] = [];
  
  for (const event of executionEvents) {
    try {
      if (event.tradingDecision) {
        const order = createOrderFromEvent(event, executorId);
        orders.push(order);
      }
    } catch (error) {
      console.error('Error creating order from event:', error);
    }
  }
  
  return orders;
};

/**
 * Finds corresponding EXECUTION events for DECISION events
 * Used to link decision-making to actual trade execution
 */
export const linkDecisionsToExecutions = (
  events: Event[]
): Map<string, string> => {
  const decisionToExecutionMap = new Map<string, string>();
  
  // Find all decision events with trading decisions
  const decisionEvents = events.filter(event => 
    event.type === 'DECISION' && 
    event.tradingDecision
  );
  
  // For each decision, find a matching execution with the same stock and action
  for (const decision of decisionEvents) {
    if (!decision.tradingDecision) continue;
    
    const { stock, action } = decision.tradingDecision;
    
    // Find execution events for the same stock and action
    const matchingExecution = events.find(event => 
      event.type === 'EXECUTION' && 
      event.tradingDecision && 
      event.tradingDecision.stock === stock && 
      event.tradingDecision.action === action &&
      event.date === decision.date // Must be on the same day
    );
    
    if (matchingExecution) {
      decisionToExecutionMap.set(decision.id, matchingExecution.id);
    }
  }
  
  return decisionToExecutionMap;
};

/**
 * Groups events by date for easy processing
 */
export const groupEventsByDate = (
  events: Event[]
): Map<string, Event[]> => {
  const eventsByDate = new Map<string, Event[]>();
  
  for (const event of events) {
    if (!eventsByDate.has(event.date)) {
      eventsByDate.set(event.date, []);
    }
    
    eventsByDate.get(event.date)?.push(event);
  }
  
  return eventsByDate;
};

/**
 * Groups orders by date for easy processing
 */
export const groupOrdersByDate = (
  orders: Order[]
): Map<string, Order[]> => {
  const ordersByDate = new Map<string, Order[]>();
  
  for (const order of orders) {
    if (!ordersByDate.has(order.date)) {
      ordersByDate.set(order.date, []);
    }
    
    ordersByDate.get(order.date)?.push(order);
  }
  
  return ordersByDate;
};

/**
 * Extracts trading decisions from events with priority to EXECUTION events
 */
export const extractTradingDecisions = (
  events: Event[]
): TradingDecision[] => {
  // First try to get decisions from execution events
  const executionDecisions = events
    .filter(event => 
      event.type === 'EXECUTION' && 
      event.tradingDecision
    )
    .map(event => event.tradingDecision as TradingDecision);
  
  // If we have execution decisions, use those
  if (executionDecisions.length > 0) {
    return executionDecisions;
  }
  
  // Otherwise fall back to regular decision events
  return events
    .filter(event => 
      event.type === 'DECISION' && 
      event.tradingDecision
    )
    .map(event => event.tradingDecision as TradingDecision);
};

// ===== START OF NEW CODE FOR PRE-GENERATED EVENTS AND TRADES =====

interface SimulatedEvent {
  timestamp: string;
  type: string;
  ticker?: string;
  message: string;
  direction?: 'up' | 'down';
  percent?: number;
  rating?: string;
  target?: number;
  action?: TradeAction;
  quantity?: number;
  price?: number;
  indicator?: string;
  actual?: number;
  forecast?: number;
  companies?: string[];
  index?: string;
  points?: number;
  sector?: string;
  agentType?: string;
}

interface TradeData {
  date: string;
  ticker: string;
  action: TradeAction;
  quantity: number;
  price: number;
  agentType: string;
}

// Cache for loaded data
let simulatedEvents: SimulatedEvent[] = [];
let tradeData: TradeData[] = [];

// Mapping ticker symbols to company names
const tickerToCompany: Record<string, string> = {
  'AMZN': 'Amazon.com Inc',
  'NVDA': 'NVIDIA Corporation',
  'MU': 'Micron Technology Inc',
  'WMT': 'Walmart Inc',
  'DIS': 'Walt Disney Company'
};

/**
 * Loads simulated events from JSON file
 */
export const loadEvents = async (): Promise<SimulatedEvent[]> => {
  if (simulatedEvents.length > 0) {
    return simulatedEvents;
  }

  try {
    console.log('Loading simulated events from data/simulated_events.json');
    const response = await fetch('data/simulated_events.json');
    if (!response.ok) {
      throw new Error(`Failed to load events: ${response.statusText}`);
    }
    const data = await response.json();
    simulatedEvents = data.events || [];
    console.log(`Successfully loaded ${simulatedEvents.length} simulated events`);
    return simulatedEvents;
  } catch (error) {
    console.error('Error loading simulated events:', error);
    return [];
  }
};

/**
 * Hardcoded trade data for one day
 */
export const loadTrades = async (): Promise<TradeData[]> => {
  console.log('Using hardcoded trade data for simulation');
  
  // Create one day of trades - using today's date
  const today = new Date();
  const dateStr = today.toISOString().split('T')[0];
  
  // Hardcoded trades for a single day
  const hardcodedTrades: TradeData[] = [
    {
      date: dateStr,
      ticker: 'NVDA',
      action: 'BUY',
      quantity: 10,
      price: 950.25,
      agentType: 'technical'
    },
    {
      date: dateStr,
      ticker: 'AMZN',
      action: 'BUY',
      quantity: 8,
      price: 178.35,
      agentType: 'fundamental'
    },
    {
      date: dateStr,
      ticker: 'MU',
      action: 'BUY',
      quantity: 20,
      price: 115.50,
      agentType: 'technical'
    },
    {
      date: dateStr,
      ticker: 'WMT',
      action: 'BUY',
      quantity: 15,
      price: 68.75,
      agentType: 'fundamental'
    },
    {
      date: dateStr,
      ticker: 'DIS',
      action: 'BUY',
      quantity: 12,
      price: 92.30,
      agentType: 'fundamental'
    },
    {
      date: dateStr,
      ticker: 'NVDA',
      action: 'SELL',
      quantity: 3,
      price: 965.75,
      agentType: 'technical'
    }
  ];
  
  tradeData = hardcodedTrades;
  console.log(`Successfully loaded ${tradeData.length} hardcoded trades for ${dateStr}`);
  return tradeData;
};

/**
 * Get events for a specific date
 */
export const getEventsForDate = (date: Date, events: SimulatedEvent[]): SimulatedEvent[] => {
  const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD format
  
  return events.filter(event => {
    const eventDate = new Date(event.timestamp);
    const eventDateStr = eventDate.toISOString().split('T')[0];
    return eventDateStr === dateStr;
  });
};

/**
 * Get trades for a specific date
 */
export const getTradesForDate = (date: Date, trades: TradeData[]): TradeData[] => {
  const dateStr = date.toISOString().split('T')[0];
  const filteredTrades = trades.filter(trade => trade.date === dateStr);
  console.log(`Found ${filteredTrades.length} trades for date ${dateStr}`);
  return filteredTrades;
};

/**
 * Process an event and update the application state
 */
export const processEvent = (event: SimulatedEvent): void => {
  // Create a unique ID for this event
  const eventId = `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Process based on event type
  switch (event.type) {
    case 'MARKET_OPEN':
    case 'MARKET_CLOSE':
    case 'NEWS':
      // Add to activity log
      store.dispatch(addLogEntry({
        id: `log-${eventId}`,
        timestamp: new Date(event.timestamp).getTime(),
        characterId: 'system',
        characterType: 'executive',
        roomId: 'system',
        actionType: 'communication',
        description: event.message,
        details: { eventType: event.type }
      }));
      break;
      
    case 'PRICE_MOVEMENT':
      if (event.ticker && event.direction && event.percent !== undefined) {
        // Add to market events
        store.dispatch(addMarketEvent({
          id: eventId,
          timestamp: new Date(event.timestamp).getTime(),
          type: 'Price Movement',
          description: event.message,
          impact: event.direction === 'up' ? 'positive' : 'negative',
          magnitude: Math.abs(event.percent) / 100
        }));
        
        // Update stock price in portfolio
        if (event.ticker && event.percent) {
          const ticker = event.ticker;
          // Get current price for this ticker from portfolio
          const state = store.getState();
          const portfolio = state.portfolio.portfolio;
          const holding = portfolio.holdings.find(h => h.stock === ticker);
          
          if (holding) {
            const currentPrice = holding.currentPrice;
            const newPrice = currentPrice * (1 + (event.direction === 'up' ? 1 : -1) * (event.percent / 100));
            
            // Update stock price
            store.dispatch(updateStockPrices({
              [ticker]: newPrice
            }));
          }
        }
        
        // Remove market event after 30 seconds
        setTimeout(() => {
          store.dispatch(removeMarketEvent(eventId));
        }, 30000);
      }
      break;
      
    case 'ANALYST_RATING':
      // Add to activity log
      store.dispatch(addLogEntry({
        id: `log-${eventId}`,
        timestamp: new Date(event.timestamp).getTime(),
        characterId: 'system',
        characterType: 'analyst',
        roomId: 'room-0', // Fundamental analysis room
        actionType: 'analysis',
        description: event.message,
        details: { 
          ticker: event.ticker,
          rating: event.rating,
          target: event.target
        }
      }));
      break;
      
    case 'ECONOMIC_DATA':
      // Add to activity log
      store.dispatch(addLogEntry({
        id: `log-${eventId}`,
        timestamp: new Date(event.timestamp).getTime(),
        characterId: 'system',
        characterType: 'executive',
        roomId: 'room-2', // CEO office
        actionType: 'analysis',
        description: event.message,
        details: { 
          indicator: event.indicator,
          actual: event.actual,
          forecast: event.forecast
        }
      }));
      break;
      
    case 'SECTOR_ROTATION':
      // Add to market events
      if (event.sector) {
        store.dispatch(addMarketEvent({
          id: eventId,
          timestamp: new Date(event.timestamp).getTime(),
          type: 'Sector Rotation',
          description: event.message,
          impact: 'neutral',
          magnitude: 0.2
        }));
        
        // Remove after 30 seconds
        setTimeout(() => {
          store.dispatch(removeMarketEvent(eventId));
        }, 30000);
      }
      break;
      
    case 'MARKET_MOVEMENT':
      // Add to market events
      if (event.index && event.points !== undefined) {
        store.dispatch(addMarketEvent({
          id: eventId,
          timestamp: new Date(event.timestamp).getTime(),
          type: 'Market Movement',
          description: event.message,
          impact: event.points >= 0 ? 'positive' : 'negative',
          magnitude: Math.abs(event.points) / 1000 // Normalize
        }));
        
        // Remove after 30 seconds
        setTimeout(() => {
          store.dispatch(removeMarketEvent(eventId));
        }, 30000);
      }
      break;
  }
};

/**
 * Process a trade and update the portfolio
 */
export const processTrade = (trade: TradeData): void => {
  // Create a unique ID
  const orderId = `order-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Format date and time
  const tradeDate = new Date(trade.date);
  // Add a random time during trading hours (9:30 AM - 4:00 PM)
  const hours = 9 + Math.floor(Math.random() * 6); // 9 to 15 (3 PM)
  const minutes = Math.floor(Math.random() * 60);
  tradeDate.setHours(hours, minutes, 0, 0);
  
  const dateStr = tradeDate.toISOString().split('T')[0];
  const timeStr = `${tradeDate.getHours().toString().padStart(2, '0')}:${tradeDate.getMinutes().toString().padStart(2, '0')}:00`;

  // Calculate total value and fees
  const totalValue = trade.quantity * trade.price;
  const fees = totalValue * 0.001; // 0.1% transaction fee
  
  // Create order
  const order: Order = {
    id: orderId,
    date: dateStr,
    time: timeStr,
    stock: trade.ticker,
    action: trade.action,
    quantity: trade.quantity,
    price: trade.price,
    status: 'PENDING' as OrderStatus,
    executedBy: trade.agentType === 'fundamental' ? 'Fundamental Analyst' : 'Technical Analyst',
    totalValue,
    fees,
    eventId: orderId // Use the same ID for now
  };

  // Add character name based on agent type
  const characterId = trade.agentType === 'fundamental' ? 'analyst-1' : 'quant-1';
  const characterName = trade.agentType === 'fundamental' ? 'Sarah Morgan' : 'David Chen';
  const characterType = trade.agentType === 'fundamental' ? 'analyst' : 'quant';
  const roomId = trade.agentType === 'fundamental' ? 'room-0' : 'room-1';
  
  // Add to order book
  store.dispatch(addOrder(order));
  
  // Add to activity log
  store.dispatch(addLogEntry({
    id: `log-${orderId}`,
    timestamp: tradeDate.getTime(),
    characterId,
    characterType,
    roomId,
    actionType: 'trading',
    description: `${characterName} ${trade.action === 'BUY' ? 'bought' : 'sold'} ${trade.quantity} shares of ${trade.ticker} at $${trade.price.toFixed(2)}`,
    details: { 
      ticker: trade.ticker,
      action: trade.action,
      quantity: trade.quantity,
      price: trade.price,
      totalValue
    }
  }));
  
  // Execute after a small delay to simulate processing
  setTimeout(() => {
    store.dispatch(executeOrder(orderId));
  }, 2000);
};

/**
 * Process daily events and trades
 */
export const processDailyData = async (date: Date): Promise<void> => {
  // Load events and trades if not already loaded
  const events = await loadEvents();
  const trades = await loadTrades();
  
  // Filter for this date
  const dailyEvents = getEventsForDate(date, events);
  const dailyTrades = getTradesForDate(date, trades);
  
  // Process events first
  dailyEvents.forEach(event => {
    processEvent(event);
  });
  
  // Then process trades
  dailyTrades.forEach(trade => {
    processTrade(trade);
  });
  
  // Generate daily performance record
  const state = store.getState();
  const portfolio = state.portfolio.portfolio;
  
  // Get latest performance record
  const latestPerformance = portfolio.performanceHistory.length > 0 
    ? portfolio.performanceHistory[portfolio.performanceHistory.length - 1] 
    : null;
    
  // Generate new performance record
  const dateStr = date.toISOString().split('T')[0];
  
  store.dispatch(addDailyPerformance({
    date: dateStr,
    totalValue: portfolio.totalValue,
    dailyChange: latestPerformance ? portfolio.totalValue - latestPerformance.totalValue : 0,
    dailyChangePercent: latestPerformance ? ((portfolio.totalValue - latestPerformance.totalValue) / latestPerformance.totalValue) * 100 : 0,
    cash: portfolio.cash,
    holdings: [...portfolio.holdings]
  }));
};
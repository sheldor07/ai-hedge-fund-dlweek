import { 
  Event, 
  Order, 
  Portfolio, 
  OrderBook, 
  Holding,
  DailyPerformance
} from '../models/types';
import { generateEventsForTimeframe } from './simulationEventLoader';
import { updateHoldingPrices, processEndOfDay } from './tradingSystem';

/**
 * Interface for the simulation state
 */
export interface SimulationState {
  startDate: Date;
  endDate: Date;
  currentDate: Date;
  portfolio: Portfolio;
  orderBook: OrderBook;
  events: Event[];
  characters: { id: string, type: string, name: string }[];
  isInitialized: boolean;
}

/**
 * Initializes the simulation with the user's investment amount and date range
 */
export const initializeSimulation = (
  investmentAmount: number,
  startDate: Date = new Date(2023, 2, 1, 8, 0, 0), // March 1, 2023, 8:00 AM
  endDate: Date = new Date(2024, 2, 1, 17, 0, 0), // March 1, 2024, 5:00 PM
  characters: { id: string, type: string, name: string }[]
): SimulationState => {
  // Format the start date as YYYY-MM-DD
  const formattedDate = startDate.toISOString().split('T')[0];
  
  // Initialize portfolio
  const portfolio: Portfolio = {
    cash: investmentAmount,
    totalValue: investmentAmount,
    holdings: [],
    performanceHistory: [{
      date: formattedDate,
      totalValue: investmentAmount,
      dailyChange: 0,
      dailyChangePercent: 0,
      cash: investmentAmount,
      holdings: []
    }]
  };
  
  // Initialize order book
  const orderBook: OrderBook = {
    orders: [],
    historicalOrders: []
  };
  
  // Generate events for the entire simulation period
  const events = generateEventsForTimeframe(startDate, endDate, characters);
  
  return {
    startDate,
    endDate,
    currentDate: new Date(startDate),
    portfolio,
    orderBook,
    events,
    characters,
    isInitialized: true
  };
};

/**
 * Processes events for a specific day
 */
export const processEventsForDay = (
  state: SimulationState,
  date: Date
): { state: SimulationState; activatedEvents: Event[] } => {
  const updatedState = { ...state };
  const formattedDate = date.toISOString().split('T')[0];
  
  // Find events for this day
  const dayEvents = updatedState.events.filter(
    event => event.date === formattedDate && !event.completed
  );
  
  // Mark these events as active/completed as appropriate
  // In a real implementation, you would handle this based on time
  dayEvents.forEach(event => {
    event.completed = true;
  });
  
  return {
    state: updatedState,
    activatedEvents: dayEvents
  };
};

/**
 * Updates the portfolio at the end of a day
 */
export const updatePortfolioForDay = async (
  state: SimulationState,
  date: Date
): Promise<SimulationState> => {
  const updatedState = { ...state };
  const formattedDate = date.toISOString().split('T')[0];
  
  // Get the most recent performance record
  const lastPerformance = updatedState.portfolio.performanceHistory.length > 0
    ? updatedState.portfolio.performanceHistory[updatedState.portfolio.performanceHistory.length - 1]
    : null;
  
  // Process end of day updates
  const { updatedHoldings, dailyPerformance } = await processEndOfDay(
    formattedDate,
    updatedState.portfolio.cash,
    updatedState.portfolio.holdings,
    lastPerformance
  );
  
  // Update the portfolio
  updatedState.portfolio.holdings = updatedHoldings;
  updatedState.portfolio.totalValue = dailyPerformance.totalValue;
  updatedState.portfolio.performanceHistory.push(dailyPerformance);
  
  return updatedState;
};

/**
 * Executes a trading decision and updates the portfolio
 */
export const executeTradingDecision = (
  state: SimulationState,
  order: Order
): SimulationState => {
  const updatedState = { ...state };
  
  // Set order status to executed
  order.status = 'EXECUTED';
  
  // Move order from active to historical
  updatedState.orderBook.historicalOrders.push({ ...order });
  updatedState.orderBook.orders = updatedState.orderBook.orders.filter(o => o.id !== order.id);
  
  // Update portfolio based on the order
  if (order.action === 'BUY') {
    // Deduct cash
    updatedState.portfolio.cash -= (order.totalValue + order.fees);
    
    // Update or add holding
    const existingHoldingIndex = updatedState.portfolio.holdings.findIndex(
      h => h.stock === order.stock
    );
    
    if (existingHoldingIndex >= 0) {
      // Update existing holding
      const existingHolding = updatedState.portfolio.holdings[existingHoldingIndex];
      const newQuantity = existingHolding.quantity + order.quantity;
      const newTotalCost = (existingHolding.quantity * existingHolding.averagePurchasePrice) + 
                           order.totalValue;
      
      // Update holding
      updatedState.portfolio.holdings[existingHoldingIndex] = {
        ...existingHolding,
        quantity: newQuantity,
        averagePurchasePrice: newTotalCost / newQuantity,
        currentValue: newQuantity * order.price,
        currentPrice: order.price,
        unrealizedPnL: 0, // Will be recalculated
        unrealizedPnLPercent: 0, // Will be recalculated
        allocation: 0 // Will be recalculated
      };
    } else {
      // Add new holding
      updatedState.portfolio.holdings.push({
        stock: order.stock,
        quantity: order.quantity,
        averagePurchasePrice: order.price,
        currentPrice: order.price,
        currentValue: order.quantity * order.price,
        unrealizedPnL: 0,
        unrealizedPnLPercent: 0,
        allocation: 0
      });
    }
  } else if (order.action === 'SELL') {
    // Add cash from sale
    updatedState.portfolio.cash += (order.totalValue - order.fees);
    
    // Update holding
    const existingHoldingIndex = updatedState.portfolio.holdings.findIndex(
      h => h.stock === order.stock
    );
    
    if (existingHoldingIndex >= 0) {
      const existingHolding = updatedState.portfolio.holdings[existingHoldingIndex];
      const newQuantity = existingHolding.quantity - order.quantity;
      
      if (newQuantity <= 0) {
        // Remove holding if all shares sold
        updatedState.portfolio.holdings = updatedState.portfolio.holdings.filter(
          (_, index) => index !== existingHoldingIndex
        );
      } else {
        // Update holding with reduced quantity
        updatedState.portfolio.holdings[existingHoldingIndex] = {
          ...existingHolding,
          quantity: newQuantity,
          currentValue: newQuantity * order.price,
          currentPrice: order.price,
          unrealizedPnL: 0, // Will be recalculated
          unrealizedPnLPercent: 0, // Will be recalculated
          allocation: 0 // Will be recalculated
        };
      }
    }
  }
  
  // Recalculate portfolio value and allocations
  const totalHoldingsValue = updatedState.portfolio.holdings.reduce(
    (sum, holding) => sum + holding.currentValue, 0
  );
  
  updatedState.portfolio.totalValue = updatedState.portfolio.cash + totalHoldingsValue;
  
  // Update allocations
  updatedState.portfolio.holdings.forEach(holding => {
    holding.allocation = (holding.currentValue / updatedState.portfolio.totalValue) * 100;
    
    // Recalculate unrealized PnL
    holding.unrealizedPnL = holding.currentValue - (holding.averagePurchasePrice * holding.quantity);
    holding.unrealizedPnLPercent = (holding.unrealizedPnL / (holding.averagePurchasePrice * holding.quantity)) * 100;
  });
  
  return updatedState;
};

/**
 * Advances the simulation by one day
 */
export const advanceSimulationByOneDay = async (
  state: SimulationState
): Promise<{
  state: SimulationState;
  dayEvents: Event[];
}> => {
  // Clone the state
  let updatedState = { ...state };
  
  // Advance the current date by one day
  const nextDate = new Date(updatedState.currentDate);
  nextDate.setDate(nextDate.getDate() + 1);
  updatedState.currentDate = nextDate;
  
  // Process events for the day
  const { state: newState, activatedEvents } = processEventsForDay(updatedState, nextDate);
  updatedState = newState;
  
  // Update portfolio at end of day
  updatedState = await updatePortfolioForDay(updatedState, nextDate);
  
  return {
    state: updatedState,
    dayEvents: activatedEvents
  };
};

/**
 * Calculates performance metrics for the portfolio
 */
export const calculatePerformanceMetrics = (portfolio: Portfolio) => {
  const history = portfolio.performanceHistory;
  
  if (history.length < 2) {
    return {
      totalReturn: 0,
      annualizedReturn: 0,
      sharpeRatio: 0,
      maxDrawdown: 0
    };
  }
  
  // Calculate total return
  const initialValue = history[0].totalValue;
  const currentValue = history[history.length - 1].totalValue;
  const totalReturn = ((currentValue - initialValue) / initialValue) * 100;
  
  // Calculate annualized return
  const daysHeld = history.length;
  const annualizedReturn = (Math.pow((1 + totalReturn / 100), (365 / daysHeld)) - 1) * 100;
  
  // Calculate daily returns for Sharpe ratio
  const dailyReturns = [];
  for (let i = 1; i < history.length; i++) {
    dailyReturns.push(history[i].dailyChangePercent);
  }
  
  // Calculate average daily return and standard deviation
  const avgDailyReturn = dailyReturns.reduce((sum, ret) => sum + ret, 0) / dailyReturns.length;
  const variance = dailyReturns.reduce((sum, ret) => sum + Math.pow(ret - avgDailyReturn, 2), 0) / dailyReturns.length;
  const stdDev = Math.sqrt(variance);
  
  // Calculate Sharpe ratio (assuming risk-free rate of 0% for simplicity)
  const sharpeRatio = stdDev > 0 ? (avgDailyReturn * Math.sqrt(252)) / stdDev : 0;
  
  // Calculate maximum drawdown
  let maxValue = history[0].totalValue;
  let maxDrawdown = 0;
  
  for (const day of history) {
    if (day.totalValue > maxValue) {
      maxValue = day.totalValue;
    }
    
    const drawdown = ((maxValue - day.totalValue) / maxValue) * 100;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  
  return {
    totalReturn: parseFloat(totalReturn.toFixed(2)),
    annualizedReturn: parseFloat(annualizedReturn.toFixed(2)),
    sharpeRatio: parseFloat(sharpeRatio.toFixed(2)),
    maxDrawdown: parseFloat(maxDrawdown.toFixed(2))
  };
};
import { 
  TradingDecision, 
  Event, 
  Order, 
  OrderStatus,
  TradeAction,
  DailyPerformance,
  Holding
} from '../models/types';

/**
 * Creates an order from a trading decision event
 */
export const createOrderFromEvent = (
  event: Event,
  executedBy: string
): Order => {
  if (!event.tradingDecision) {
    throw new Error('Event does not contain a trading decision');
  }
  
  const { tradingDecision } = event;
  const { stock, action, quantity, price } = tradingDecision;
  
  // Calculate total value and fees
  const totalValue = quantity * price;
  const fees = totalValue * 0.001; // 0.1% transaction fee
  
  // Format date and time for the order
  const [hours, minutes] = event.time.split(':');
  const orderTime = `${hours}:${minutes}:00`;
  
  return {
    id: `order-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    date: event.date,
    time: orderTime,
    stock,
    action,
    quantity,
    price,
    status: 'PENDING',
    executedBy,
    totalValue,
    fees,
    eventId: event.id
  };
};

/**
 * Fetches current stock price from an API or uses mock data
 * In a real application, this would call an external API
 */
export const fetchStockPrice = async (
  ticker: string,
  date: string,
  priceType: 'open' | 'close' | 'high' | 'low' = 'close'
): Promise<number> => {
  // Mock price data for demonstration
  const mockPrices: { [key: string]: number } = {
    'AMZN': 178.35,
    'NVDA': 822.79,
    'MU': 94.42,
    'WMT': 59.68,
    'DIS': 111.95
  };
  
  // Add some random variation (+/- 2%)
  const basePrice = mockPrices[ticker] || 100;
  const variation = basePrice * (0.98 + Math.random() * 0.04);
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  
  return Number(variation.toFixed(2));
};

/**
 * Updates portfolio holdings with current market prices
 */
export const updateHoldingPrices = async (
  holdings: Holding[]
): Promise<Holding[]> => {
  const updatedHoldings = [...holdings];
  
  // Get today's date in YYYY-MM-DD format
  const today = new Date().toISOString().split('T')[0];
  
  // Update each holding with current price
  for (const holding of updatedHoldings) {
    const currentPrice = await fetchStockPrice(holding.stock, today);
    holding.currentPrice = currentPrice;
    holding.currentValue = holding.quantity * currentPrice;
    holding.unrealizedPnL = holding.currentValue - (holding.averagePurchasePrice * holding.quantity);
    holding.unrealizedPnLPercent = (holding.unrealizedPnL / (holding.averagePurchasePrice * holding.quantity)) * 100;
  }
  
  return updatedHoldings;
};

/**
 * Generates daily performance record
 */
export const generateDailyPerformance = (
  date: string,
  prevPerformance: DailyPerformance | null,
  cash: number,
  holdings: Holding[]
): DailyPerformance => {
  // Calculate total value
  const holdingsValue = holdings.reduce((sum, holding) => sum + holding.currentValue, 0);
  const totalValue = cash + holdingsValue;
  
  // Calculate daily change
  let dailyChange = 0;
  let dailyChangePercent = 0;
  
  if (prevPerformance) {
    dailyChange = totalValue - prevPerformance.totalValue;
    dailyChangePercent = (dailyChange / prevPerformance.totalValue) * 100;
  }
  
  return {
    date,
    totalValue,
    dailyChange,
    dailyChangePercent,
    cash,
    holdings: [...holdings] // Make a copy of holdings
  };
};

/**
 * Process end of day portfolio updates
 */
export const processEndOfDay = async (
  date: string,
  cash: number,
  holdings: Holding[],
  lastPerformance: DailyPerformance | null
): Promise<{
  updatedHoldings: Holding[],
  dailyPerformance: DailyPerformance
}> => {
  // Update holdings with closing prices
  const updatedHoldings = await updateHoldingPrices(holdings);
  
  // Generate daily performance record
  const dailyPerformance = generateDailyPerformance(
    date,
    lastPerformance,
    cash,
    updatedHoldings
  );
  
  return {
    updatedHoldings,
    dailyPerformance
  };
};
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface PortfolioHolding {
  companyId: string;
  ticker: string;
  name: string;
  sharesHeld: number;
  currentPrice: number;
  purchasePrice: number;
  lastUpdated: number;
}

export interface Transaction {
  id: string;
  timestamp: number;
  formattedDate: string;
  action: 'buy' | 'sell' | 'hold';
  ticker: string;
  shares: number;
  price: number;
  decisionMaker: string;
}

export interface PortfolioMetrics {
  totalValue: number;
  cashAvailable: number;
  dailyReturn: number;
  monthlyReturn: number;
  ytdReturn: number;
  alpha: number;
  beta: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
}

export interface CashFlow {
  id: string;
  timestamp: number;
  amount: number;
  type: 'deposit' | 'withdrawal' | 'dividend' | 'interest';
  description: string;
}

interface PortfolioState {
  holdings: PortfolioHolding[];
  transactions: Transaction[];
  cashFlows: CashFlow[];
  metrics: PortfolioMetrics;
  selectedTimeRange: '1D' | '1W' | '1M' | '3M' | 'YTD' | '1Y' | 'ALL';
  historicalPerformance: {
    timestamp: number;
    value: number;
  }[];
}

// Sample initial data for the mock portfolio
const initialState: PortfolioState = {
  holdings: [
    {
      companyId: 'amzn',
      ticker: 'AMZN',
      name: 'Amazon',
      sharesHeld: 500,
      currentPrice: 178.75,
      purchasePrice: 145.20,
      lastUpdated: Date.now(),
    },
    {
      companyId: 'nvda',
      ticker: 'NVDA',
      name: 'NVIDIA',
      sharesHeld: 300,
      currentPrice: 822.79,
      purchasePrice: 710.50,
      lastUpdated: Date.now(),
    },
    {
      companyId: 'mu',
      ticker: 'MU',
      name: 'Micron',
      sharesHeld: 1200,
      currentPrice: 94.42,
      purchasePrice: 72.15,
      lastUpdated: Date.now(),
    },
    {
      companyId: 'wmt',
      ticker: 'WMT',
      name: 'Walmart',
      sharesHeld: 800,
      currentPrice: 59.68,
      purchasePrice: 54.30,
      lastUpdated: Date.now(),
    },
    {
      companyId: 'dis',
      ticker: 'DIS',
      name: 'Walt Disney',
      sharesHeld: 650,
      currentPrice: 111.95,
      purchasePrice: 98.75,
      lastUpdated: Date.now(),
    },
  ],
  transactions: [
    {
      id: 't1',
      timestamp: Date.now() - 86400000 * 2,
      formattedDate: '2024-02-28',
      action: 'buy',
      ticker: 'AMZN',
      shares: 200,
      price: 145.20,
      decisionMaker: 'Fundamental Analyst',
    },
    {
      id: 't2',
      timestamp: Date.now() - 86400000 * 4,
      formattedDate: '2024-02-26',
      action: 'buy',
      ticker: 'NVDA',
      shares: 150,
      price: 710.50,
      decisionMaker: 'Quant Trader',
    },
    {
      id: 't3',
      timestamp: Date.now() - 86400000 * 7,
      formattedDate: '2024-02-23',
      action: 'buy',
      ticker: 'MU',
      shares: 500,
      price: 72.15,
      decisionMaker: 'Risk Manager',
    },
    {
      id: 't4',
      timestamp: Date.now() - 86400000 * 10,
      formattedDate: '2024-02-20',
      action: 'sell',
      ticker: 'DIS',
      shares: 150,
      price: 104.30,
      decisionMaker: 'Executive',
    },
    {
      id: 't5',
      timestamp: Date.now() - 86400000 * 12,
      formattedDate: '2024-02-18',
      action: 'buy',
      ticker: 'WMT',
      shares: 300,
      price: 54.30,
      decisionMaker: 'Fundamental Analyst',
    },
    {
      id: 't6',
      timestamp: Date.now() - 86400000 * 15,
      formattedDate: '2024-02-15',
      action: 'buy',
      ticker: 'AMZN',
      shares: 300,
      price: 142.75,
      decisionMaker: 'Quant Trader',
    },
    {
      id: 't7',
      timestamp: Date.now() - 86400000 * 18,
      formattedDate: '2024-02-12',
      action: 'buy',
      ticker: 'NVDA',
      shares: 150,
      price: 680.25,
      decisionMaker: 'Executive',
    },
    {
      id: 't8',
      timestamp: Date.now() - 86400000 * 20,
      formattedDate: '2024-02-10',
      action: 'hold',
      ticker: 'MU',
      shares: 0,
      price: 80.45,
      decisionMaker: 'Risk Manager',
    },
    {
      id: 't9',
      timestamp: Date.now() - 86400000 * 22,
      formattedDate: '2024-02-08',
      action: 'buy',
      ticker: 'DIS',
      shares: 250,
      price: 98.75,
      decisionMaker: 'Fundamental Analyst',
    },
    {
      id: 't10',
      timestamp: Date.now() - 86400000 * 25,
      formattedDate: '2024-02-05',
      action: 'buy',
      ticker: 'MU',
      shares: 700,
      price: 78.30,
      decisionMaker: 'Quant Trader',
    },
    {
      id: 't11',
      timestamp: Date.now() - 86400000 * 28,
      formattedDate: '2024-02-02',
      action: 'buy',
      ticker: 'WMT',
      shares: 500,
      price: 58.15,
      decisionMaker: 'Executive',
    },
    {
      id: 't12',
      timestamp: Date.now() - 86400000 * 30,
      formattedDate: '2024-01-31',
      action: 'sell',
      ticker: 'NVDA',
      shares: 100,
      price: 650.80,
      decisionMaker: 'Risk Manager',
    },
    {
      id: 't13',
      timestamp: Date.now() - 86400000 * 35,
      formattedDate: '2024-01-26',
      action: 'buy',
      ticker: 'DIS',
      shares: 550,
      price: 95.40,
      decisionMaker: 'Fundamental Analyst',
    },
    {
      id: 't14',
      timestamp: Date.now() - 86400000 * 40,
      formattedDate: '2024-01-21',
      action: 'hold',
      ticker: 'AMZN',
      shares: 0,
      price: 140.25,
      decisionMaker: 'Quant Trader',
    },
    {
      id: 't15',
      timestamp: Date.now() - 86400000 * 45,
      formattedDate: '2024-01-16',
      action: 'buy',
      ticker: 'NVDA',
      shares: 100,
      price: 620.40,
      decisionMaker: 'Executive',
    },
  ],
  cashFlows: [
    {
      id: 'cf1',
      timestamp: Date.now() - 86400000 * 5,
      amount: 250000,
      type: 'deposit',
      description: 'Initial funding allocation',
    },
    {
      id: 'cf2',
      timestamp: Date.now() - 86400000 * 10,
      amount: 15600,
      type: 'withdrawal',
      description: 'Portfolio rebalancing',
    },
    {
      id: 'cf3',
      timestamp: Date.now() - 86400000 * 20,
      amount: 3250,
      type: 'dividend',
      description: 'WMT quarterly dividend',
    },
    {
      id: 'cf4',
      timestamp: Date.now() - 86400000 * 30,
      amount: 1875,
      type: 'interest',
      description: 'Interest on cash reserves',
    },
  ],
  metrics: {
    totalValue: 1275000,
    cashAvailable: 325000,
    dailyReturn: 1.2,
    monthlyReturn: 4.5,
    ytdReturn: 12.8,
    alpha: 2.4,
    beta: 1.15,
    sharpeRatio: 1.8,
    maxDrawdown: -8.5,
    volatility: 15.2,
  },
  selectedTimeRange: '1M',
  historicalPerformance: Array.from({ length: 180 }, (_, i) => {
    // Generate sample performance data for the last 180 days
    const date = new Date();
    date.setDate(date.getDate() - (180 - i));
    
    // Create a realistic-looking growth trend with some volatility
    const baseValue = 1000000;
    const trendGrowth = i * 2000;
    const volatility = Math.random() * 40000 - 20000;
    
    // Add some weekly pattern (markets typically go up on Fridays, down on Mondays)
    const dayOfWeek = date.getDay();
    const weekendEffect = dayOfWeek === 5 ? 5000 : dayOfWeek === 1 ? -5000 : 0;
    
    // Add some monthly pattern (end of month window dressing)
    const dayOfMonth = date.getDate();
    const monthEndEffect = dayOfMonth >= 28 ? 10000 : 0;
    
    // Combine all effects
    const value = baseValue + trendGrowth + volatility + weekendEffect + monthEndEffect;
    
    return {
      timestamp: date.getTime(),
      value: Math.max(value, 950000), // Ensure we don't go below a reasonable floor
    };
  }),
};

export const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    updateHolding: (state, action: PayloadAction<PortfolioHolding>) => {
      const index = state.holdings.findIndex(
        (holding) => holding.companyId === action.payload.companyId
      );
      
      if (index !== -1) {
        state.holdings[index] = action.payload;
      } else {
        state.holdings.push(action.payload);
      }
    },
    addTransaction: (state, action: PayloadAction<Transaction>) => {
      state.transactions.unshift(action.payload);
    },
    addCashFlow: (state, action: PayloadAction<CashFlow>) => {
      state.cashFlows.unshift(action.payload);
    },
    updateMetrics: (state, action: PayloadAction<Partial<PortfolioMetrics>>) => {
      state.metrics = { ...state.metrics, ...action.payload };
    },
    setSelectedTimeRange: (
      state,
      action: PayloadAction<'1D' | '1W' | '1M' | '3M' | 'YTD' | '1Y' | 'ALL'>
    ) => {
      state.selectedTimeRange = action.payload;
    },
    addHistoricalDataPoint: (state, action: PayloadAction<{ timestamp: number; value: number }>) => {
      state.historicalPerformance.push(action.payload);
    },
  },
});

export const {
  updateHolding,
  addTransaction,
  addCashFlow,
  updateMetrics,
  setSelectedTimeRange,
  addHistoricalDataPoint,
} = portfolioSlice.actions;

export default portfolioSlice.reducer;
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  Holding, 
  DailyPerformance, 
  Portfolio, 
  Order, 
  OrderBook, 
  TradeAction
} from '../models/types';

interface PortfolioState {
  portfolio: Portfolio;
  orderBook: OrderBook;
  selectedTimeRange: '1D' | '1W' | '1M' | '3M' | 'YTD' | '1Y' | 'ALL';
}

// Initial state with default values
const initialState: PortfolioState = {
  portfolio: {
    cash: 1000000, // $1 million initial investment
    totalValue: 1000000,
    holdings: [],
    performanceHistory: []
  },
  orderBook: {
    orders: [],
    historicalOrders: []
  },
  selectedTimeRange: '1M',
};

export const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    // Initialize portfolio with investment amount
    initializePortfolio: (state, action: PayloadAction<number>) => {
      state.portfolio.cash = action.payload;
      state.portfolio.totalValue = action.payload;
      state.portfolio.holdings = [];
      state.portfolio.performanceHistory = [{
        date: new Date().toISOString().split('T')[0],
        totalValue: action.payload,
        dailyChange: 0,
        dailyChangePercent: 0,
        cash: action.payload,
        holdings: []
      }];
    },
    
    // Update or add a holding
    updateHolding: (state, action: PayloadAction<Holding>) => {
      const index = state.portfolio.holdings.findIndex(
        (holding) => holding.stock === action.payload.stock
      );
      
      if (index !== -1) {
        state.portfolio.holdings[index] = action.payload;
      } else {
        state.portfolio.holdings.push(action.payload);
      }
      
      // Recalculate total portfolio value
      const holdingsValue = state.portfolio.holdings.reduce(
        (sum, holding) => sum + holding.currentValue, 0
      );
      state.portfolio.totalValue = state.portfolio.cash + holdingsValue;
      
      // Update allocation percentages
      state.portfolio.holdings.forEach(holding => {
        holding.allocation = (holding.currentValue / state.portfolio.totalValue) * 100;
      });
    },
    
    // Add a new order to the order book
    addOrder: (state, action: PayloadAction<Order>) => {
      state.orderBook.orders.push(action.payload);
    },
    
    // Execute an order (move from active to historical and update portfolio)
    executeOrder: (state, action: PayloadAction<string>) => {
      const orderIndex = state.orderBook.orders.findIndex(
        order => order.id === action.payload
      );
      
      if (orderIndex !== -1) {
        const order = state.orderBook.orders[orderIndex];
        
        // Update order status
        order.status = 'EXECUTED';
        
        // Move to historical orders
        state.orderBook.historicalOrders.push(order);
        state.orderBook.orders.splice(orderIndex, 1);
        
        // Update portfolio based on the order
        if (order.action === 'BUY') {
          // Deduct cash
          state.portfolio.cash -= order.totalValue + order.fees;
          
          // Update or add holding
          const holdingIndex = state.portfolio.holdings.findIndex(
            holding => holding.stock === order.stock
          );
          
          if (holdingIndex !== -1) {
            // Update existing holding
            const holding = state.portfolio.holdings[holdingIndex];
            const totalShares = holding.quantity + order.quantity;
            const totalCost = (holding.quantity * holding.averagePurchasePrice) + 
                             (order.quantity * order.price);
            
            holding.quantity = totalShares;
            holding.averagePurchasePrice = totalCost / totalShares;
            holding.currentPrice = order.price; // Use most recent price
            holding.currentValue = holding.quantity * holding.currentPrice;
            holding.unrealizedPnL = holding.currentValue - (holding.averagePurchasePrice * holding.quantity);
            holding.unrealizedPnLPercent = (holding.unrealizedPnL / (holding.averagePurchasePrice * holding.quantity)) * 100;
          } else {
            // Add new holding
            state.portfolio.holdings.push({
              stock: order.stock,
              quantity: order.quantity,
              averagePurchasePrice: order.price,
              currentPrice: order.price,
              currentValue: order.quantity * order.price,
              unrealizedPnL: 0,
              unrealizedPnLPercent: 0,
              allocation: 0 // Will be updated below
            });
          }
        } else if (order.action === 'SELL') {
          // Add cash
          state.portfolio.cash += order.totalValue - order.fees;
          
          // Update holding
          const holdingIndex = state.portfolio.holdings.findIndex(
            holding => holding.stock === order.stock
          );
          
          if (holdingIndex !== -1) {
            const holding = state.portfolio.holdings[holdingIndex];
            holding.quantity -= order.quantity;
            
            // If all shares sold, remove the holding
            if (holding.quantity <= 0) {
              state.portfolio.holdings.splice(holdingIndex, 1);
            } else {
              // Otherwise update current value and PnL
              holding.currentPrice = order.price; // Use most recent price
              holding.currentValue = holding.quantity * holding.currentPrice;
              holding.unrealizedPnL = holding.currentValue - (holding.averagePurchasePrice * holding.quantity);
              holding.unrealizedPnLPercent = (holding.unrealizedPnL / (holding.averagePurchasePrice * holding.quantity)) * 100;
            }
          }
        }
        
        // Recalculate total portfolio value
        const holdingsValue = state.portfolio.holdings.reduce(
          (sum, holding) => sum + holding.currentValue, 0
        );
        state.portfolio.totalValue = state.portfolio.cash + holdingsValue;
        
        // Update allocation percentages
        state.portfolio.holdings.forEach(holding => {
          holding.allocation = (holding.currentValue / state.portfolio.totalValue) * 100;
        });
      }
    },
    
    // Cancel an order
    cancelOrder: (state, action: PayloadAction<string>) => {
      const orderIndex = state.orderBook.orders.findIndex(
        order => order.id === action.payload
      );
      
      if (orderIndex !== -1) {
        const order = state.orderBook.orders[orderIndex];
        order.status = 'CANCELLED';
        state.orderBook.historicalOrders.push(order);
        state.orderBook.orders.splice(orderIndex, 1);
      }
    },
    
    // Add daily performance record
    addDailyPerformance: (state, action: PayloadAction<DailyPerformance>) => {
      state.portfolio.performanceHistory.push(action.payload);
      
      // Limit history size if needed
      if (state.portfolio.performanceHistory.length > 365) {
        state.portfolio.performanceHistory.shift();
      }
    },
    
    // Update all stock prices and recalculate portfolio
    updateStockPrices: (state, action: PayloadAction<{[ticker: string]: number}>) => {
      // Update each holding with new price
      state.portfolio.holdings.forEach(holding => {
        if (action.payload[holding.stock]) {
          const newPrice = action.payload[holding.stock];
          holding.currentPrice = newPrice;
          holding.currentValue = holding.quantity * newPrice;
          holding.unrealizedPnL = holding.currentValue - (holding.averagePurchasePrice * holding.quantity);
          holding.unrealizedPnLPercent = (holding.unrealizedPnL / (holding.averagePurchasePrice * holding.quantity)) * 100;
        }
      });
      
      // Recalculate total portfolio value
      const holdingsValue = state.portfolio.holdings.reduce(
        (sum, holding) => sum + holding.currentValue, 0
      );
      state.portfolio.totalValue = state.portfolio.cash + holdingsValue;
      
      // Update allocation percentages
      state.portfolio.holdings.forEach(holding => {
        holding.allocation = (holding.currentValue / state.portfolio.totalValue) * 100;
      });
    },
    
    setSelectedTimeRange: (
      state,
      action: PayloadAction<'1D' | '1W' | '1M' | '3M' | 'YTD' | '1Y' | 'ALL'>
    ) => {
      state.selectedTimeRange = action.payload;
    },
  },
});

export const {
  initializePortfolio,
  updateHolding,
  addOrder,
  executeOrder,
  cancelOrder,
  addDailyPerformance,
  updateStockPrices,
  setSelectedTimeRange,
} = portfolioSlice.actions;

export default portfolioSlice.reducer;
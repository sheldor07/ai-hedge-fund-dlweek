import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setCurrentView } from '../store/simulationSlice';
import { setSelectedTimeRange } from '../store/portfolioSlice';
import {
  Portfolio as PortfolioType,
  Holding,
  Order,
  OrderStatus,
  TradeAction,
  DailyPerformance
} from '../models/types';

interface HoldingWithAllocation extends Holding {
  currentValue: number;
  allocationPercentage: number;
  profitLoss: number;
  profitLossPercentage: number;
  name?: string;
  ticker?: string;
  companyId?: string;
  sharesHeld: number;
  currentPrice: number;
  purchasePrice: number;
}

interface CashFlow {
  id: string;
  timestamp: number;
  type: 'deposit' | 'withdrawal' | 'dividend' | 'interest';
  amount: number;
  description: string;
}

interface PortfolioMetrics {
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

interface HistoricalDataPoint {
  timestamp: number;
  value: number;
}

interface PortfolioState {
  holdings: HoldingWithAllocation[];
  metrics: PortfolioMetrics;
  transactions: Array<{
    id: string;
    action: 'buy' | 'sell' | 'hold';
    ticker: string;
    shares: number;
    price: number;
    formattedDate: string;
    timestamp: number;
    decisionMaker: string;
  }>;
  historicalPerformance: HistoricalDataPoint[];
  cashFlows: CashFlow[];
  selectedTimeRange: '1D' | '1W' | '1M' | '3M' | 'YTD' | '1Y' | 'ALL';
}

const Portfolio: React.FC = () => {
  const dispatch = useDispatch();
  const portfolioState = useSelector((state: RootState) => state.portfolio as unknown as PortfolioState);
  const [activeTab, setActiveTab] = useState<'holdings' | 'orders' | 'performance' | 'cash'>('holdings');
  const [orderBookFilter, setOrderBookFilter] = useState<{
    action: 'all' | 'buy' | 'sell' | 'hold';
    ticker: string | null;
    dateRange: { start: number | null; end: number | null };
  }>({
    action: 'all',
    ticker: null,
    dateRange: { start: null, end: null },
  });

  // Calculate derived data
  const totalPortfolioValue = portfolioState.holdings.reduce(
    (sum: number, holding: HoldingWithAllocation) => sum + (holding.sharesHeld || holding.quantity) * holding.currentPrice,
    0
  );

  const totalPortfolioValueWithCash = totalPortfolioValue + portfolioState.metrics.cashAvailable;

  // Calculate allocation percentages
  const holdingsWithAllocation = portfolioState.holdings.map((holding: HoldingWithAllocation) => {
    const currentValue = (holding.sharesHeld || holding.quantity) * holding.currentPrice;
    const allocationPercentage = (currentValue / totalPortfolioValueWithCash) * 100;
    const profitLoss = (holding.currentPrice - (holding.purchasePrice || holding.averagePurchasePrice)) * (holding.sharesHeld || holding.quantity);
    const profitLossPercentage = ((holding.currentPrice - (holding.purchasePrice || holding.averagePurchasePrice)) / (holding.purchasePrice || holding.averagePurchasePrice)) * 100;
    
    return {
      ...holding,
      currentValue,
      allocationPercentage,
      profitLoss,
      profitLossPercentage,
      sharesHeld: holding.sharesHeld || holding.quantity,
      purchasePrice: holding.purchasePrice || holding.averagePurchasePrice
    };
  });

  // Function to filter order book
  const filteredTransactions = portfolioState.transactions.filter((transaction) => {
    // Filter by action
    if (orderBookFilter.action !== 'all' && transaction.action !== orderBookFilter.action) {
      return false;
    }
    
    // Filter by ticker
    if (orderBookFilter.ticker && transaction.ticker !== orderBookFilter.ticker) {
      return false;
    }
    
    // Filter by date range
    if (orderBookFilter.dateRange.start && transaction.timestamp < orderBookFilter.dateRange.start) {
      return false;
    }
    
    if (orderBookFilter.dateRange.end && transaction.timestamp > orderBookFilter.dateRange.end) {
      return false;
    }
    
    return true;
  });

  // Return to office view
  const handleReturnToOffice = (): void => {
    dispatch(setCurrentView('office'));
  };

  // Time range selector buttons
  const timeRangeButtons: { label: string; value: '1D' | '1W' | '1M' | '3M' | 'YTD' | '1Y' | 'ALL' }[] = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: 'YTD', value: 'YTD' },
    { label: '1Y', value: '1Y' },
    { label: 'ALL', value: 'ALL' },
  ];

  // Render holdings table
  const renderHoldingsTable = () => {
    // Calculate totals for the summary row
    const totalValue = holdingsWithAllocation.reduce(
      (sum: number, holding: HoldingWithAllocation) => sum + holding.currentValue,
      0
    );
    
    const totalProfitLoss = holdingsWithAllocation.reduce(
      (sum: number, holding: HoldingWithAllocation) => sum + holding.profitLoss,
      0
    );
    
    const avgProfitLossPercentage = 
      (totalProfitLoss / (totalValue - totalProfitLoss)) * 100;
    
    return (
      <div style={{ width: '100%' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '15px',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: '0 0 0 0', color: '#4caf50' }}>Portfolio Holdings</h2>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            fontSize: '1.1em',
            fontWeight: 'bold',
          }}>
            <span>Total Portfolio Value: </span>
            <span style={{ marginLeft: '10px', color: '#4caf50' }}>
              ${totalPortfolioValueWithCash.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
          </div>
        </div>
        
        {/* Holdings pie chart */}
        <div style={{ 
          marginBottom: '20px', 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '10px',
          padding: '15px',
        }}>
          <div style={{ 
            width: '250px', 
            height: '250px', 
            position: 'relative',
            borderRadius: '50%',
            background: 'conic-gradient(#4caf50 0%, #4caf50 25%, #2196f3 25%, #2196f3 40%, #ff9800 40%, #ff9800 55%, #f44336 55%, #f44336 70%, #9c27b0 70%, #9c27b0 85%, #e0e0e0 85%, #e0e0e0 100%)',
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
          }}>
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '120px',
              height: '120px',
              background: 'white',
              borderRadius: '50%',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontWeight: 'bold',
              fontSize: '1.2em',
              color: '#333',
              boxShadow: 'inset 0 2px 5px rgba(0,0,0,0.1)'
            }}>
              Portfolio
            </div>
          </div>
          
          <div style={{ 
            width: 'calc(100% - 290px)',
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '10px'
          }}>
            {holdingsWithAllocation.map((holding, index) => (
              <div key={holding.companyId} style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px',
                borderLeft: `4px solid ${
                  index === 0 ? '#4caf50' : 
                  index === 1 ? '#2196f3' : 
                  index === 2 ? '#ff9800' : 
                  index === 3 ? '#f44336' : 
                  index === 4 ? '#9c27b0' : '#e0e0e0'
                }`
              }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '4px',
                  background: index === 0 ? '#4caf50' : 
                    index === 1 ? '#2196f3' : 
                    index === 2 ? '#ff9800' : 
                    index === 3 ? '#f44336' : 
                    index === 4 ? '#9c27b0' : '#e0e0e0',
                  marginRight: '10px'
                }}></div>
                <div>
                  <div style={{ fontWeight: 'bold' }}>{holding.ticker}</div>
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    {holding.allocationPercentage.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              padding: '10px',
              borderLeft: '4px solid #e0e0e0'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '4px',
                background: '#e0e0e0',
                marginRight: '10px'
              }}></div>
              <div>
                <div style={{ fontWeight: 'bold' }}>Cash</div>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  {((portfolioState.metrics.cashAvailable / totalPortfolioValueWithCash) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Holdings table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            background: 'rgba(255, 255, 255, 0.8)',
            borderRadius: '10px',
            overflow: 'hidden',
          }}>
            <thead>
              <tr style={{ 
                background: '#4caf50', 
                color: 'white',
                fontSize: '0.9em',
                textAlign: 'left',
              }}>
                <th style={{ padding: '12px 15px' }}>Company</th>
                <th style={{ padding: '12px 15px' }}>Ticker</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Shares</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Current Price</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Current Value</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Purchase Price</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Profit/Loss ($)</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Profit/Loss (%)</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Allocation (%)</th>
              </tr>
            </thead>
            <tbody>
              {holdingsWithAllocation.map((holding) => (
                <tr key={holding.companyId} style={{ 
                  borderBottom: '1px solid #eee',
                  fontSize: '0.9em',
                }}>
                  <td style={{ padding: '10px 15px', fontWeight: 'bold' }}>{holding.name}</td>
                  <td style={{ padding: '10px 15px' }}>{holding.ticker}</td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>{(holding.sharesHeld || holding.quantity).toLocaleString()}</td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    ${holding.currentPrice.toFixed(2)}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    ${((holding.sharesHeld || holding.quantity) * holding.currentPrice).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    ${(holding.purchasePrice || holding.averagePurchasePrice).toFixed(2)}
                  </td>
                  <td style={{ 
                    padding: '10px 15px', 
                    textAlign: 'right',
                    color: holding.profitLoss >= 0 ? '#4caf50' : '#f44336',
                  }}>
                    ${Math.abs(holding.profitLoss).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    {holding.profitLoss >= 0 ? ' ▲' : ' ▼'}
                  </td>
                  <td style={{ 
                    padding: '10px 15px', 
                    textAlign: 'right',
                    color: holding.profitLossPercentage >= 0 ? '#4caf50' : '#f44336',
                  }}>
                    {Math.abs(holding.profitLossPercentage).toFixed(2)}%
                    {holding.profitLossPercentage >= 0 ? ' ▲' : ' ▼'}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    {holding.allocationPercentage.toFixed(2)}%
                  </td>
                </tr>
              ))}
              <tr style={{ 
                borderTop: '2px solid #ddd',
                background: 'rgba(76, 175, 80, 0.1)',
                fontWeight: 'bold',
              }}>
                <td style={{ padding: '10px 15px' }}>Cash</td>
                <td style={{ padding: '10px 15px' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                  ${portfolioState.metrics.cashAvailable.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                  {((portfolioState.metrics.cashAvailable / totalPortfolioValueWithCash) * 100).toFixed(2)}%
                </td>
              </tr>
              <tr style={{ 
                borderTop: '2px solid #ddd',
                background: 'rgba(76, 175, 80, 0.2)',
                fontWeight: 'bold',
              }}>
                <td style={{ padding: '10px 15px' }}>TOTAL</td>
                <td style={{ padding: '10px 15px' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                  ${totalPortfolioValueWithCash.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>-</td>
                <td style={{ 
                  padding: '10px 15px', 
                  textAlign: 'right',
                  color: totalProfitLoss >= 0 ? '#4caf50' : '#f44336',
                }}>
                  ${Math.abs(totalProfitLoss).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  {totalProfitLoss >= 0 ? ' ▲' : ' ▼'}
                </td>
                <td style={{ 
                  padding: '10px 15px', 
                  textAlign: 'right',
                  color: avgProfitLossPercentage >= 0 ? '#4caf50' : '#f44336',
                }}>
                  {Math.abs(avgProfitLossPercentage).toFixed(2)}%
                  {avgProfitLossPercentage >= 0 ? ' ▲' : ' ▼'}
                </td>
                <td style={{ padding: '10px 15px', textAlign: 'right' }}>100.00%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Render order book table
  const renderOrderBook = () => {
    return (
      <div style={{ width: '100%' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '15px',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: '0 0 0 0', color: '#4caf50' }}>Order Book</h2>
          <div style={{ 
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}>
            {/* Filter dropdown for action */}
            <select 
              value={orderBookFilter.action}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setOrderBookFilter({
                ...orderBookFilter, 
                action: e.target.value as 'all' | 'buy' | 'sell' | 'hold'
              })}
              style={{
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                background: 'white',
              }}
            >
              <option value="all">All Actions</option>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
              <option value="hold">Hold</option>
            </select>
            
            {/* Filter dropdown for ticker */}
            <select 
              value={orderBookFilter.ticker || ''}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setOrderBookFilter({
                ...orderBookFilter, 
                ticker: e.target.value || null
              })}
              style={{
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                background: 'white',
              }}
            >
              <option value="">All Tickers</option>
              <option value="AMZN">AMZN</option>
              <option value="NVDA">NVDA</option>
              <option value="MU">MU</option>
              <option value="WMT">WMT</option>
              <option value="DIS">DIS</option>
            </select>
          </div>
        </div>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            background: 'rgba(255, 255, 255, 0.8)',
            borderRadius: '10px',
            overflow: 'hidden',
          }}>
            <thead>
              <tr style={{ 
                background: '#4caf50', 
                color: 'white',
                fontSize: '0.9em',
                textAlign: 'left',
              }}>
                <th style={{ padding: '12px 15px' }}>Date</th>
                <th style={{ padding: '12px 15px' }}>Action</th>
                <th style={{ padding: '12px 15px' }}>Ticker</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Shares</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Price</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Total Value</th>
                <th style={{ padding: '12px 15px' }}>Decision Maker</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((transaction) => (
                <tr key={transaction.id} style={{ 
                  borderBottom: '1px solid #eee',
                  fontSize: '0.9em',
                }}>
                  <td style={{ padding: '10px 15px' }}>{transaction.formattedDate}</td>
                  <td style={{ padding: '10px 15px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '0.8em',
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                      color: 'white',
                      background: 
                        transaction.action === 'buy' ? '#4caf50' :
                        transaction.action === 'sell' ? '#f44336' :
                        '#2196f3',
                    }}>
                      {transaction.action}
                    </span>
                  </td>
                  <td style={{ padding: '10px 15px', fontWeight: 'bold' }}>{transaction.ticker}</td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    {transaction.shares.toLocaleString()}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    ${transaction.price.toFixed(2)}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'right' }}>
                    ${(transaction.shares * transaction.price).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td style={{ padding: '10px 15px' }}>{transaction.decisionMaker}</td>
                </tr>
              ))}
              {filteredTransactions.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ 
                    padding: '20px', 
                    textAlign: 'center',
                    color: '#666',
                  }}>
                    No transactions match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Render performance metrics
  const renderPerformanceMetrics = () => {
    // Sample historical data for chart
    const chartData = portfolioState.historicalPerformance;
    const dataPoints = chartData.length;
    const maxValue = Math.max(...chartData.map((point: HistoricalDataPoint) => point.value));
    const minValue = Math.min(...chartData.map((point: HistoricalDataPoint) => point.value));
    const range = maxValue - minValue;
    
    // Calculate metrics summary boxes
    const metricBoxes: { label: string; value: string }[] = [
      { label: 'Daily Return', value: `${portfolioState.metrics.dailyReturn.toFixed(2)}%` },
      { label: 'Monthly Return', value: `${portfolioState.metrics.monthlyReturn.toFixed(2)}%` },
      { label: 'YTD Return', value: `${portfolioState.metrics.ytdReturn.toFixed(2)}%` },
      { label: 'Alpha', value: portfolioState.metrics.alpha.toFixed(2) },
      { label: 'Beta', value: portfolioState.metrics.beta.toFixed(2) },
      { label: 'Sharpe Ratio', value: portfolioState.metrics.sharpeRatio.toFixed(2) },
      { label: 'Max Drawdown', value: `${portfolioState.metrics.maxDrawdown.toFixed(2)}%` },
      { label: 'Volatility', value: `${portfolioState.metrics.volatility.toFixed(2)}%` },
    ];

    return (
      <div style={{ width: '100%' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '15px',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: '0 0 0 0', color: '#4caf50' }}>Performance Metrics</h2>
          <div style={{ 
            display: 'flex',
            gap: '5px',
          }}>
            {timeRangeButtons.map(button => (
              <button
                key={button.value}
                onClick={() => dispatch(setSelectedTimeRange(button.value as any))}
                style={{
                  padding: '6px 12px',
                  borderRadius: '4px',
                  border: 'none',
                  background: portfolioState.selectedTimeRange === button.value 
                    ? '#4caf50' 
                    : 'rgba(255, 255, 255, 0.8)',
                  color: portfolioState.selectedTimeRange === button.value 
                    ? 'white' 
                    : '#333',
                  cursor: 'pointer',
                  fontWeight: portfolioState.selectedTimeRange === button.value 
                    ? 'bold' 
                    : 'normal',
                }}
              >
                {button.label}
              </button>
            ))}
          </div>
        </div>
        
        {/* Chart */}
        <div style={{
          marginBottom: '20px',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '10px',
          padding: '20px',
        }}>
          <div style={{ 
            height: '300px', 
            position: 'relative',
            marginBottom: '10px',
          }}>
            {/* Y-axis labels */}
            <div style={{
              position: 'absolute',
              left: 0,
              top: 0,
              height: '100%',
              width: '60px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              fontSize: '0.8em',
              color: '#666',
              padding: '5px 0',
            }}>
              <div>${Math.round(maxValue / 1000)}K</div>
              <div>${Math.round((maxValue - range/3) / 1000)}K</div>
              <div>${Math.round((maxValue - 2*range/3) / 1000)}K</div>
              <div>${Math.round(minValue / 1000)}K</div>
            </div>
            
            {/* Chart area */}
            <div style={{
              marginLeft: '60px',
              height: '100%',
              position: 'relative',
              borderBottom: '1px solid #ddd',
              borderLeft: '1px solid #ddd',
            }}>
              {/* Grid lines */}
              <div style={{
                position: 'absolute',
                left: 0,
                top: 0,
                width: '100%',
                height: '25%',
                borderBottom: '1px dashed #ddd',
              }}></div>
              <div style={{
                position: 'absolute',
                left: 0,
                top: '33.33%',
                width: '100%',
                height: '25%',
                borderBottom: '1px dashed #ddd',
              }}></div>
              <div style={{
                position: 'absolute',
                left: 0,
                top: '66.66%',
                width: '100%',
                height: '25%',
                borderBottom: '1px dashed #ddd',
              }}></div>
              
              {/* Chart line */}
              <svg
                width="100%"
                height="100%"
                viewBox={`0 0 ${dataPoints} 100`}
                preserveAspectRatio="none"
                style={{ position: 'absolute', left: 0, top: 0 }}
              >
                <defs>
                  <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="rgba(76, 175, 80, 0.5)" />
                    <stop offset="100%" stopColor="rgba(76, 175, 80, 0)" />
                  </linearGradient>
                </defs>
                
                {/* Area fill */}
                <path
                  d={`
                    M 0 ${100 - ((chartData[0].value - minValue) / range) * 100}
                    ${chartData.map((point: HistoricalDataPoint, i: number) => {
                      const x = (i / (dataPoints - 1)) * dataPoints;
                      const y = 100 - ((point.value - minValue) / range) * 100;
                      return `L ${x} ${y}`;
                    }).join(' ')}
                    L ${dataPoints} 100
                    L 0 100
                    Z
                  `}
                  fill="url(#chartGradient)"
                />
                
                {/* Line */}
                <path
                  d={`
                    M 0 ${100 - ((chartData[0].value - minValue) / range) * 100}
                    ${chartData.map((point: HistoricalDataPoint, i: number) => {
                      const x = (i / (dataPoints - 1)) * dataPoints;
                      const y = 100 - ((point.value - minValue) / range) * 100;
                      return `L ${x} ${y}`;
                    }).join(' ')}
                  `}
                  stroke="#4caf50"
                  strokeWidth="2"
                  fill="none"
                />
              </svg>
            </div>
          </div>
          
          {/* X-axis labels */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginLeft: '60px',
            fontSize: '0.8em',
            color: '#666',
          }}>
            {Array.from({ length: 6 }).map((_, i) => {
              const date = new Date(chartData[Math.floor(i * (dataPoints - 1) / 5)].timestamp);
              return (
                <div key={i}>
                  {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Metrics summary */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '15px',
          marginBottom: '20px',
        }}>
          {metricBoxes.map((metric, index) => (
            <div key={index} style={{
              background: 'rgba(255, 255, 255, 0.8)',
              borderRadius: '10px',
              padding: '15px',
              textAlign: 'center',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            }}>
              <div style={{ 
                fontSize: '0.9em', 
                color: '#666', 
                marginBottom: '5px' 
              }}>
                {metric.label}
              </div>
              <div style={{ 
                fontSize: '1.3em', 
                fontWeight: 'bold',
                color: (
                  metric.label.includes('Return') || 
                  metric.label === 'Alpha' || 
                  metric.label === 'Sharpe Ratio'
                ) && parseFloat(metric.value) > 0
                  ? '#4caf50'
                  : metric.label === 'Max Drawdown' || (
                    (metric.label.includes('Return') || 
                    metric.label === 'Alpha' || 
                    metric.label === 'Sharpe Ratio') && 
                    parseFloat(metric.value) < 0
                  )
                    ? '#f44336'
                    : '#333',
              }}>
                {metric.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render cash position
  const renderCashPosition = () => {
    const cashPercentage = (portfolioState.metrics.cashAvailable / totalPortfolioValueWithCash) * 100;
    
    return (
      <div style={{ width: '100%' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '15px',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: '0 0 0 0', color: '#4caf50' }}>Cash Position</h2>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            fontSize: '1.1em',
            fontWeight: 'bold',
          }}>
            <span>Available Cash: </span>
            <span style={{ marginLeft: '10px', color: '#4caf50' }}>
              ${portfolioState.metrics.cashAvailable.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
          </div>
        </div>
        
        {/* Cash status indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '20px',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '10px',
          padding: '20px',
        }}>
          <div style={{
            width: '150px',
            height: '150px',
            borderRadius: '50%',
            background: `conic-gradient(#4caf50 0%, #4caf50 ${cashPercentage}%, #e0e0e0 ${cashPercentage}%, #e0e0e0 100%)`,
            position: 'relative',
            marginRight: '30px',
          }}>
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'white',
              borderRadius: '50%',
              width: '110px',
              height: '110px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
            }}>
              <div style={{ fontSize: '1.6em', fontWeight: 'bold', color: '#4caf50' }}>
                {cashPercentage.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.8em', color: '#666' }}>
                Cash
              </div>
            </div>
          </div>
          
          <div style={{ flex: 1 }}>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ fontSize: '1.1em', fontWeight: 'bold', marginBottom: '5px' }}>
                Cash Allocation
              </div>
              <div style={{ fontSize: '0.9em', color: '#666', lineHeight: '1.5' }}>
                Your portfolio currently has {cashPercentage.toFixed(1)}% allocated to cash reserves.
                This provides liquidity for new investment opportunities and helps manage risk.
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '1.1em', fontWeight: 'bold', marginBottom: '5px' }}>
                Recommended Actions
              </div>
              <div style={{ fontSize: '0.9em', color: '#666', lineHeight: '1.5' }}>
                {cashPercentage > 30 
                  ? 'Your cash position is high. Consider investing in new opportunities to maximize returns.'
                  : cashPercentage < 10
                    ? 'Your cash position is low. Consider rebalancing to increase liquidity for future opportunities.'
                    : 'Your cash position is within the optimal range. No immediate action needed.'}
              </div>
            </div>
          </div>
        </div>
        
        {/* Cash flow history */}
        <h3 style={{ color: '#4caf50', marginBottom: '15px' }}>Recent Cash Flows</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            background: 'rgba(255, 255, 255, 0.8)',
            borderRadius: '10px',
            overflow: 'hidden',
          }}>
            <thead>
              <tr style={{ 
                background: '#4caf50', 
                color: 'white',
                fontSize: '0.9em',
                textAlign: 'left',
              }}>
                <th style={{ padding: '12px 15px' }}>Date</th>
                <th style={{ padding: '12px 15px' }}>Type</th>
                <th style={{ padding: '12px 15px', textAlign: 'right' }}>Amount</th>
                <th style={{ padding: '12px 15px' }}>Description</th>
              </tr>
            </thead>
            <tbody>
              {portfolioState.cashFlows.map((cashFlow: CashFlow) => {
                const date = new Date(cashFlow.timestamp);
                return (
                  <tr key={cashFlow.id} style={{ 
                    borderBottom: '1px solid #eee',
                    fontSize: '0.9em',
                  }}>
                    <td style={{ padding: '10px 15px' }}>
                      {date.toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </td>
                    <td style={{ padding: '10px 15px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '0.8em',
                        fontWeight: 'bold',
                        textTransform: 'uppercase',
                        color: 'white',
                        background: 
                          cashFlow.type === 'deposit' ? '#4caf50' :
                          cashFlow.type === 'withdrawal' ? '#f44336' :
                          cashFlow.type === 'dividend' ? '#ff9800' :
                          '#2196f3',
                      }}>
                        {cashFlow.type}
                      </span>
                    </td>
                    <td style={{ 
                      padding: '10px 15px', 
                      textAlign: 'right',
                      color: ['deposit', 'dividend', 'interest'].includes(cashFlow.type) 
                        ? '#4caf50' : '#f44336',
                    }}>
                      {['deposit', 'dividend', 'interest'].includes(cashFlow.type) ? '+' : '-'}
                      ${cashFlow.amount.toLocaleString(undefined, { 
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td style={{ padding: '10px 15px' }}>{cashFlow.description}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div 
      style={{
        width: '100%',
        height: '100vh',
        display: 'flex',
        background: '#f0f0f0',
        fontFamily: 'Arial, sans-serif',
      }}
    >
      {/* Main content */}
      <div 
        style={{
          width: '100%',
          height: '100%',
          padding: '20px',
          overflowY: 'auto',
        }}
      >
        {/* Breadcrumbs */}
        <div style={{ marginBottom: '20px' }}>
          <span 
            style={{ cursor: 'pointer', color: '#4caf50' }}
            onClick={handleReturnToOffice}
          >
            Office
          </span>
          <span style={{ margin: '0 5px' }}>/</span>
          <span style={{ fontWeight: 'bold' }}>Portfolio & Order Book</span>
        </div>
        
        {/* Portfolio header */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '20px',
          }}
        >
          <div 
            style={{ 
              width: '80px', 
              height: '80px',
              background: '#4caf50',
              borderRadius: '10px',
              marginRight: '20px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontWeight: 'bold',
              fontSize: '2em',
              color: 'white',
            }}
          >
            📊
          </div>
          <div>
            <h1 style={{ margin: '0 0 5px 0' }}>Portfolio & Order Book</h1>
            <div style={{ color: '#666' }}>
              Overview of the fund's investments, transactions, and performance metrics
            </div>
          </div>
        </div>
        
        {/* Tabs navigation */}
        <div style={{ 
          display: 'flex',
          borderBottom: '2px solid #4caf50',
          marginBottom: '20px',
        }}>
          {[
            { id: 'holdings', label: 'Holdings' },
            { id: 'orders', label: 'Order Book' },
            { id: 'performance', label: 'Performance' },
            { id: 'cash', label: 'Cash Position' },
          ].map(tab => (
            <div 
              key={tab.id}
              style={{
                padding: '12px 20px',
                cursor: 'pointer',
                fontWeight: activeTab === tab.id ? 'bold' : 'normal',
                borderBottom: activeTab === tab.id ? '3px solid #4caf50' : 'none',
                color: activeTab === tab.id ? '#4caf50' : '#333',
                background: activeTab === tab.id ? 'rgba(76, 175, 80, 0.1)' : 'transparent',
                borderTopLeftRadius: '5px',
                borderTopRightRadius: '5px',
                marginBottom: activeTab === tab.id ? '-2px' : '0',
              }}
              onClick={() => setActiveTab(tab.id as any)}
            >
              {tab.label}
            </div>
          ))}
        </div>
        
        {/* Tab content */}
        <div style={{ 
          background: 'rgba(76, 175, 80, 0.05)', 
          borderRadius: '10px',
          padding: '20px',
        }}>
          {activeTab === 'holdings' && renderHoldingsTable()}
          {activeTab === 'orders' && renderOrderBook()}
          {activeTab === 'performance' && renderPerformanceMetrics()}
          {activeTab === 'cash' && renderCashPosition()}
        </div>
      </div>
    </div>
  );
};

export default Portfolio;
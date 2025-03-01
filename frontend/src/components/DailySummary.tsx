import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { fastForwardToNextDay, fastForwardToNextWeekday } from '../store/simulationSlice';
import { DailyPerformance, Event, Order } from '../models/types';

interface DailySummaryProps {
  date: Date;
  onClose: () => void;
}

const DailySummary: React.FC<DailySummaryProps> = ({ date, onClose }) => {
  const dispatch = useDispatch();
  
  // Get simulation events for the day
  const events = useSelector((state: RootState) => 
    state.simulation.completedCharacterEvents.filter(
      event => {
        const eventDate = new Date(event.timestamp);
        return eventDate.toDateString() === date.toDateString();
      }
    )
  );
  
  // Get portfolio performance for the day
  const performanceHistory = useSelector((state: RootState) => 
    state.portfolio.portfolio.performanceHistory
  );
  
  // Get orders executed on this day
  const historicalOrders = useSelector((state: RootState) => 
    state.portfolio.orderBook.historicalOrders
  );
  
  // Format date to YYYY-MM-DD for comparison
  const dateStr = date.toISOString().split('T')[0];
  
  // Find performance data for this specific day
  const todayPerformance = performanceHistory.find(p => p.date === dateStr);
  
  // Find orders for this specific day
  const todayOrders = historicalOrders.filter(order => order.date === dateStr);
  
  // Group events by type
  const analyzedStocks = events
    .filter(event => event.eventType === 'ANALYZE')
    .map(event => event.relatedStock)
    .filter((stock, index, self) => stock && self.indexOf(stock) === index);
  
  const decisions = events
    .filter(event => event.eventType === 'DECIDE');
  
  // Handle continue to next day
  const handleContinueToNextDay = () => {
    dispatch(fastForwardToNextDay());
    onClose();
  };
  
  // Handle skip to next weekday
  const handleSkipToNextWeekday = () => {
    dispatch(fastForwardToNextWeekday());
    onClose();
  };
  
  // Format date
  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };
  
  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '20px',
        width: '80%',
        maxWidth: '700px',
        maxHeight: '80%',
        overflowY: 'auto',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
      }}>
        <h2 style={{ 
          marginTop: 0, 
          borderBottom: '2px solid #f0f0f0',
          paddingBottom: '10px',
          color: '#2196f3'
        }}>
          Daily Summary: {formatDate(date)}
        </h2>
        
        {/* Portfolio Performance Section */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: '#333' }}>Portfolio Performance</h3>
          
          {todayPerformance ? (
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap',
              gap: '15px',
              backgroundColor: '#f9f9f9',
              padding: '15px',
              borderRadius: '8px'
            }}>
              <div style={{ textAlign: 'center', flex: '1 0 30%' }}>
                <div style={{ fontSize: '12px', color: '#666' }}>Total Value</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {formatCurrency(todayPerformance.totalValue)}
                </div>
              </div>
              
              <div style={{ textAlign: 'center', flex: '1 0 30%' }}>
                <div style={{ fontSize: '12px', color: '#666' }}>Daily Change</div>
                <div style={{ 
                  fontSize: '18px', 
                  fontWeight: 'bold',
                  color: todayPerformance.dailyChange >= 0 ? '#4caf50' : '#f44336'
                }}>
                  {formatCurrency(todayPerformance.dailyChange)} 
                  ({todayPerformance.dailyChangePercent.toFixed(2)}%)
                </div>
              </div>
              
              <div style={{ textAlign: 'center', flex: '1 0 30%' }}>
                <div style={{ fontSize: '12px', color: '#666' }}>Cash Balance</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {formatCurrency(todayPerformance.cash)}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '15px' }}>
              No performance data available for this day
            </div>
          )}
        </div>
        
        {/* Trading Activity Section */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: '#333' }}>Trading Activity</h3>
          
          {todayOrders.length > 0 ? (
            <div style={{ 
              backgroundColor: '#f9f9f9',
              padding: '15px',
              borderRadius: '8px'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Stock</th>
                    <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Action</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Quantity</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Price</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Total Value</th>
                  </tr>
                </thead>
                <tbody>
                  {todayOrders.map((order, index) => (
                    <tr key={index}>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{order.stock}</td>
                      <td style={{ 
                        padding: '8px', 
                        borderBottom: '1px solid #eee',
                        color: order.action === 'BUY' ? '#4caf50' : '#f44336'
                      }}>
                        {order.action}
                      </td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {order.quantity.toLocaleString()}
                      </td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {formatCurrency(order.price)}
                      </td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {formatCurrency(order.totalValue)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '15px' }}>
              No trades executed today
            </div>
          )}
        </div>
        
        {/* Analysis Activity Section */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: '#333' }}>Analysis Activity</h3>
          
          <div style={{ marginBottom: '15px' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Analyzed Stocks:</div>
            {analyzedStocks.length > 0 ? (
              <div style={{ 
                display: 'flex', 
                flexWrap: 'wrap', 
                gap: '8px'
              }}>
                {analyzedStocks.map((stock, index) => (
                  <span key={index} style={{
                    backgroundColor: '#e3f2fd',
                    color: '#0d47a1',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}>
                    {stock}
                  </span>
                ))}
              </div>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic' }}>No stocks analyzed today</div>
            )}
          </div>
          
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Key Decisions:</div>
            {decisions.length > 0 ? (
              <ul style={{ 
                margin: 0, 
                paddingLeft: '20px',
                color: '#333'
              }}>
                {decisions.slice(0, 5).map((decision, index) => (
                  <li key={index}>
                    {decision.message}
                    {decision.relatedStock && (
                      <span style={{ 
                        backgroundColor: '#e8f5e9', 
                        color: '#2e7d32',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        marginLeft: '8px'
                      }}>
                        {decision.relatedStock}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic' }}>No decisions made today</div>
            )}
          </div>
        </div>
        
        {/* Holdings Summary */}
        {todayPerformance && todayPerformance.holdings.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ color: '#333' }}>Current Holdings</h3>
            <div style={{ 
              backgroundColor: '#f9f9f9',
              padding: '15px',
              borderRadius: '8px',
              maxHeight: '200px',
              overflowY: 'auto'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Stock</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Shares</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Avg. Price</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Current Value</th>
                    <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {todayPerformance.holdings.map((holding, index) => (
                    <tr key={index}>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{holding.stock}</td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {holding.quantity.toLocaleString()}
                      </td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {formatCurrency(holding.averagePurchasePrice)}
                      </td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {formatCurrency(holding.currentValue)}
                      </td>
                      <td style={{ 
                        padding: '8px', 
                        borderBottom: '1px solid #eee', 
                        textAlign: 'right',
                        color: holding.unrealizedPnL >= 0 ? '#4caf50' : '#f44336'
                      }}>
                        {formatCurrency(holding.unrealizedPnL)} 
                        ({holding.unrealizedPnLPercent.toFixed(2)}%)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* Navigation Buttons */}
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          justifyContent: 'center',
          marginTop: '20px',
          borderTop: '1px solid #f0f0f0',
          paddingTop: '20px'
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '12px 15px',
              backgroundColor: '#e0e0e0',
              color: '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              flex: 1,
              fontWeight: 'bold'
            }}
          >
            Continue at Current Pace
          </button>
          
          <button
            onClick={handleContinueToNextDay}
            style={{
              padding: '12px 15px',
              backgroundColor: '#ff9800',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              flex: 1,
              fontWeight: 'bold'
            }}
          >
            Skip to Next Day
          </button>
          
          <button
            onClick={handleSkipToNextWeekday}
            style={{
              padding: '12px 15px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              flex: 1,
              fontWeight: 'bold'
            }}
          >
            Skip to Next Weekday
          </button>
        </div>
      </div>
    </div>
  );
};

export default DailySummary;
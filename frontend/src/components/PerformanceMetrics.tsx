import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const PerformanceMetrics: React.FC = () => {
  const performanceMetrics = useSelector(
    (state: RootState) => state.simulation.performanceMetrics
  );
  const currentMarketEvents = useSelector(
    (state: RootState) => state.simulation.currentMarketEvents
  );

  // Helper functions to calculate latest metrics
  const getLatestMetric = (metricType: 'return' | 'alpha' | 'sharpe' | 'drawdown') => {
    const metrics = performanceMetrics[metricType];
    if (metrics.length === 0) return 0;
    return metrics[metrics.length - 1].value;
  };

  // Format percentages
  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  // Format ratio
  const formatRatio = (value: number) => {
    return value.toFixed(2);
  };

  return (
    <div className="performance-metrics">
      <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Fund Performance</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <div>Return:</div>
          <div style={{ fontWeight: 'bold', color: getLatestMetric('return') >= 0 ? 'green' : 'red' }}>
            {formatPercentage(getLatestMetric('return'))}
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <div>Alpha:</div>
          <div style={{ fontWeight: 'bold', color: getLatestMetric('alpha') >= 0 ? 'green' : 'red' }}>
            {formatPercentage(getLatestMetric('alpha'))}
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <div>Sharpe Ratio:</div>
          <div style={{ fontWeight: 'bold' }}>
            {formatRatio(getLatestMetric('sharpe'))}
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div>Max Drawdown:</div>
          <div style={{ fontWeight: 'bold', color: 'red' }}>
            {formatPercentage(getLatestMetric('drawdown'))}
          </div>
        </div>
      </div>
      
      {currentMarketEvents.length > 0 && (
        <>
          <h4 style={{ margin: '10px 0', fontSize: '14px' }}>Current Market Events</h4>
          <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
            {currentMarketEvents.map((event) => (
              <div 
                key={event.id} 
                style={{ 
                  marginBottom: '5px', 
                  padding: '5px',
                  backgroundColor: 
                    event.impact === 'positive' ? 'rgba(0, 255, 0, 0.1)' : 
                    event.impact === 'negative' ? 'rgba(255, 0, 0, 0.1)' : 
                    'rgba(255, 255, 0, 0.1)',
                  borderRadius: '3px',
                  fontSize: '12px'
                }}
              >
                <div style={{ fontWeight: 'bold' }}>{event.type}</div>
                <div>{event.description}</div>
              </div>
            ))}
          </div>
        </>
      )}
      
      <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default PerformanceMetrics;
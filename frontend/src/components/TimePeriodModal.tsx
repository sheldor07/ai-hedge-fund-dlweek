import React, { useState } from 'react';
import { useDispatch } from 'react-redux';

interface TimePeriodModalProps {
  onComplete: (startDate: Date, endDate: Date) => void;
  onBack: () => void;
}

const TimePeriodModal: React.FC<TimePeriodModalProps> = ({ onComplete, onBack }) => {
  // Fixed start date: March 1, 2023
  const startDate = new Date(2023, 2, 1);
  
  // Initial end date: March 1, 2024 (12 months)
  const maxEndDate = new Date(2024, 2, 1);
  
  // State for selected end date
  const [endDate, setEndDate] = useState(maxEndDate);
  
  // State for months (1-12)
  const [months, setMonths] = useState(12);
  
  // Calculate months between dates
  const calculateMonths = (start: Date, end: Date): number => {
    return (end.getFullYear() - start.getFullYear()) * 12 + 
           (end.getMonth() - start.getMonth());
  };
  
  // Handle slider change for months
  const handleMonthsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMonths = parseInt(e.target.value);
    setMonths(newMonths);
    
    // Calculate new end date
    const newEndDate = new Date(startDate);
    newEndDate.setMonth(startDate.getMonth() + newMonths);
    setEndDate(newEndDate);
  };
  
  // Format date for display
  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };
  
  // Handle start simulation button click
  const handleStartSimulation = () => {
    onComplete(startDate, endDate);
  };
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 9999
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '30px',
        width: '90%',
        maxWidth: '500px',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)'
      }}>
        <h2 style={{
          margin: '0 0 20px 0',
          fontSize: '1.8rem',
          color: '#1976d2',
          textAlign: 'center'
        }}>
          For how long would you like to invest?
        </h2>
        
        {/* Time period visualization */}
        <div style={{
          position: 'relative',
          height: '100px',
          marginBottom: '25px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          {/* Timeline bar */}
          <div style={{
            width: '100%',
            height: '6px',
            backgroundColor: '#e0e0e0',
            borderRadius: '3px',
            position: 'relative'
          }}>
            {/* Filled timeline */}
            <div style={{
              position: 'absolute',
              left: 0,
              top: 0,
              height: '100%',
              width: `${(months / 12) * 100}%`,
              backgroundColor: '#2196f3',
              borderRadius: '3px',
              transition: 'width 0.3s ease'
            }} />
            
            {/* Start marker */}
            <div style={{
              position: 'absolute',
              left: 0,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              backgroundColor: '#2196f3',
              border: '2px solid white',
              boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
              zIndex: 2
            }} />
            
            {/* End marker */}
            <div style={{
              position: 'absolute',
              left: `${(months / 12) * 100}%`,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              backgroundColor: '#2196f3',
              border: '2px solid white',
              boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
              zIndex: 2
            }} />
          </div>
          
          {/* Date labels */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '15px',
            fontSize: '0.9rem',
            color: '#333'
          }}>
            <div>
              <div style={{ fontWeight: 'bold' }}>Start Date</div>
              <div>{formatDate(startDate)}</div>
            </div>
            
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 'bold' }}>End Date</div>
              <div>{formatDate(endDate)}</div>
            </div>
          </div>
        </div>
        
        {/* Months slider */}
        <div style={{ marginBottom: '30px' }}>
          <label style={{
            display: 'block',
            marginBottom: '10px',
            fontWeight: 'bold',
            color: '#333'
          }}>
            Investment Duration: <span style={{ color: '#1976d2' }}>{months} month{months !== 1 ? 's' : ''}</span>
          </label>
          
          <input
            type="range"
            min={1}
            max={12}
            value={months}
            onChange={handleMonthsChange}
            style={{
              width: '100%',
              height: '8px',
              appearance: 'none',
              backgroundColor: '#e0e0e0',
              borderRadius: '4px',
              outline: 'none',
              cursor: 'pointer'
            }}
          />
          
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '5px',
            fontSize: '0.8rem',
            color: '#666'
          }}>
            <span>1 month</span>
            <span>12 months</span>
          </div>
        </div>
        
        {/* Expected return information */}
        <div style={{
          backgroundColor: '#f5f5f5',
          padding: '15px',
          borderRadius: '4px',
          marginBottom: '25px'
        }}>
          <div style={{
            fontWeight: 'bold',
            marginBottom: '5px',
            color: '#333'
          }}>
            Expected Performance:
          </div>
          
          <div style={{
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>Estimated Return:</div>
              <div style={{ 
                fontSize: '1.1rem', 
                fontWeight: 'bold', 
                color: '#4caf50'
              }}>
                {/* Simple mock return calculation based on duration */}
                +{(8 + Math.min(months, 6) * 0.5).toFixed(1)}%
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>Estimated Risk:</div>
              <div style={{ 
                fontSize: '1.1rem', 
                fontWeight: 'bold', 
                color: months > 9 ? '#4caf50' : months > 6 ? '#ff9800' : '#f44336'
              }}>
                {/* Simple mock risk level based on duration */}
                {months > 9 ? 'Low' : months > 6 ? 'Medium' : 'High'}
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>Sharpe Ratio:</div>
              <div style={{ 
                fontSize: '1.1rem', 
                fontWeight: 'bold', 
                color: '#1976d2'
              }}>
                {/* Simple mock Sharpe ratio based on duration */}
                {(1.2 + months * 0.05).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
        
        {/* Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '15px'
        }}>
          <button
            onClick={onBack}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: '#e0e0e0',
              color: '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: 'bold'
            }}
          >
            Back
          </button>
          
          <button
            onClick={handleStartSimulation}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: 'bold'
            }}
          >
            Start Simulation
          </button>
        </div>
      </div>
    </div>
  );
};

export default TimePeriodModal;
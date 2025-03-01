import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';

interface InvestmentModalProps {
  onNext: (investmentAmount: number) => void;
  onCancel: () => void;
}

const InvestmentModal: React.FC<InvestmentModalProps> = ({ onNext, onCancel }) => {
  const [investmentAmount, setInvestmentAmount] = useState(1000000);
  const [displayAmount, setDisplayAmount] = useState('1,000,000');
  const [error, setError] = useState('');
  
  // Min/Max values
  const MIN_INVESTMENT = 100000;
  const MAX_INVESTMENT = 10000000;
  
  // Format the investment amount with commas for thousands
  const formatAmount = (value: number): string => {
    return value.toLocaleString('en-US');
  };
  
  // Handle slider change
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    setInvestmentAmount(value);
    setDisplayAmount(formatAmount(value));
    setError('');
  };
  
  // Handle input change with validation
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Remove commas and other non-numeric characters
    const rawValue = e.target.value.replace(/[^0-9]/g, '');
    const value = rawValue === '' ? 0 : parseInt(rawValue);
    
    setDisplayAmount(rawValue === '' ? '' : formatAmount(value));
    setInvestmentAmount(value);
    
    // Validate input
    if (value < MIN_INVESTMENT) {
      setError(`Minimum investment is $${formatAmount(MIN_INVESTMENT)}`);
    } else if (value > MAX_INVESTMENT) {
      setError(`Maximum investment is $${formatAmount(MAX_INVESTMENT)}`);
    } else {
      setError('');
    }
  };
  
  // Handle Next button click
  const handleNext = () => {
    if (investmentAmount < MIN_INVESTMENT || investmentAmount > MAX_INVESTMENT) {
      return; // Don't proceed if amount is invalid
    }
    onNext(investmentAmount);
  };
  
  // Calculate coin stack size based on investment amount
  const coinSize = Math.min(Math.max(investmentAmount / MAX_INVESTMENT, 0.2), 1) * 100;
  
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
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
        position: 'relative'
      }}>
        <h2 style={{
          margin: '0 0 20px 0',
          fontSize: '1.8rem',
          color: '#1976d2',
          textAlign: 'center'
        }}>
          How much would you like to invest with us?
        </h2>
        
        {/* Investment visualization */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '25px',
          height: '100px',
          alignItems: 'flex-end'
        }}>
          {/* Simple coin stack visualization */}
          <div style={{
            position: 'relative',
            width: '100px',
            height: '100px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} style={{
                position: 'absolute',
                bottom: i * 12,
                width: `${coinSize}px`,
                height: '20px',
                borderRadius: '50%',
                background: 'linear-gradient(to bottom, #ffd700 0%, #ffc107 100%)',
                border: '1px solid rgba(0,0,0,0.1)',
                boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                transition: 'width 0.3s ease, bottom 0.3s ease',
                transform: 'perspective(200px) rotateX(60deg)',
                zIndex: 5 - i
              }} />
            ))}
          </div>
        </div>
        
        {/* Input field */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontWeight: 'bold',
            color: '#333'
          }}>
            Investment Amount:
          </label>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            position: 'relative'
          }}>
            <span style={{
              position: 'absolute',
              left: '15px',
              fontSize: '1.2rem',
              color: '#555'
            }}>$</span>
            
            <input
              type="text"
              value={displayAmount}
              onChange={handleInputChange}
              style={{
                width: '100%',
                padding: '12px 15px 12px 30px',
                fontSize: '1.2rem',
                border: `1px solid ${error ? '#f44336' : '#ccc'}`,
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
          </div>
          
          {error && (
            <div style={{
              color: '#f44336',
              fontSize: '0.9rem',
              marginTop: '5px'
            }}>
              {error}
            </div>
          )}
        </div>
        
        {/* Slider */}
        <div style={{ marginBottom: '30px' }}>
          <input
            type="range"
            min={MIN_INVESTMENT}
            max={MAX_INVESTMENT}
            step={10000}
            value={investmentAmount}
            onChange={handleSliderChange}
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
            <span>${formatAmount(MIN_INVESTMENT)}</span>
            <span>${formatAmount(MAX_INVESTMENT)}</span>
          </div>
        </div>
        
        {/* Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '15px'
        }}>
          <button
            onClick={onCancel}
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
            Cancel
          </button>
          
          <button
            onClick={handleNext}
            disabled={!!error}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: error ? '#cccccc' : '#2196f3',
              color: error ? '#666' : 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: error ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: 'bold'
            }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default InvestmentModal;
import React, { useState, useEffect } from 'react';

interface TutorialTooltipProps {
  step: number;
  position: {
    top?: string;
    bottom?: string;
    left?: string;
    right?: string;
  };
  content: string;
  onComplete: () => void;
  autoClose?: boolean;
  autoCloseTime?: number;
}

const TutorialTooltip: React.FC<TutorialTooltipProps> = ({
  step,
  position,
  content,
  onComplete,
  autoClose = false,
  autoCloseTime = 5000
}) => {
  const [visible, setVisible] = useState(true);
  
  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(() => {
        setVisible(false);
        onComplete();
      }, autoCloseTime);
      
      return () => clearTimeout(timer);
    }
  }, [autoClose, autoCloseTime, onComplete]);
  
  const handleClose = () => {
    setVisible(false);
    onComplete();
  };
  
  if (!visible) return null;
  
  return (
    <div
      style={{
        position: Object.keys(position).length > 0 ? 'absolute' : 'relative',
        ...position,
        backgroundColor: 'white',
        color: '#333',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
        borderRadius: '8px',
        padding: '15px',
        maxWidth: '300px',
        zIndex: 1000,
        animation: 'fadeIn 0.3s ease-in-out',
        border: '2px solid #2196f3'
      }}
    >
      {/* Step indicator */}
      <div
        style={{
          position: 'absolute',
          top: '-10px',
          left: '-10px',
          backgroundColor: '#2196f3',
          color: 'white',
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          fontWeight: 'bold',
          fontSize: '14px',
          boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)'
        }}
      >
        {step}
      </div>
      
      {/* Content */}
      <p style={{ margin: '0 0 15px 0', lineHeight: '1.5' }}>
        {content}
      </p>
      
      {/* Button */}
      <button
        onClick={handleClose}
        style={{
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          padding: '8px 15px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: 'bold'
        }}
      >
        Got it
      </button>
      
      {/* Arrow */}
      {position.bottom !== undefined && (
        <div
          style={{
            position: 'absolute',
            bottom: '-10px',
            left: '50%',
            transform: 'translateX(-50%) rotate(45deg)',
            width: '20px',
            height: '20px',
            backgroundColor: 'white',
            borderRight: '2px solid #2196f3',
            borderBottom: '2px solid #2196f3',
            zIndex: -1
          }}
        />
      )}
      
      {position.top !== undefined && (
        <div
          style={{
            position: 'absolute',
            top: '-10px',
            left: '50%',
            transform: 'translateX(-50%) rotate(45deg)',
            width: '20px',
            height: '20px',
            backgroundColor: 'white',
            borderLeft: '2px solid #2196f3',
            borderTop: '2px solid #2196f3',
            zIndex: -1
          }}
        />
      )}
      
      {position.left !== undefined && (
        <div
          style={{
            position: 'absolute',
            left: '-10px',
            top: '50%',
            transform: 'translateY(-50%) rotate(45deg)',
            width: '20px',
            height: '20px',
            backgroundColor: 'white',
            borderLeft: '2px solid #2196f3',
            borderBottom: '2px solid #2196f3',
            zIndex: -1
          }}
        />
      )}
      
      {position.right !== undefined && (
        <div
          style={{
            position: 'absolute',
            right: '-10px',
            top: '50%',
            transform: 'translateY(-50%) rotate(45deg)',
            width: '20px',
            height: '20px',
            backgroundColor: 'white',
            borderRight: '2px solid #2196f3',
            borderTop: '2px solid #2196f3',
            zIndex: -1
          }}
        />
      )}
    </div>
  );
};

export default TutorialTooltip;
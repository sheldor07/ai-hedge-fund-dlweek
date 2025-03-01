import React, { useEffect, useState } from 'react';

interface LoadingScreenProps {
  onLoadingComplete: () => void;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ onLoadingComplete }) => {
  const [progress, setProgress] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState('Loading Assets...');
  
  // Force the body to have overflow hidden during loading to prevent scrolling
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    
    // Hide any potential html elements from three.js that might be visible
    const threejsElements = document.querySelectorAll('.drei-html');
    threejsElements.forEach(el => {
      if (el instanceof HTMLElement) {
        el.style.display = 'none';
      }
    });
    
    return () => {
      document.body.style.overflow = '';
      threejsElements.forEach(el => {
        if (el instanceof HTMLElement) {
          el.style.display = '';
        }
      });
    };
  }, []);
  
  useEffect(() => {
    const loadingMessages = [
      { message: 'Loading Assets...', threshold: 0 },
      { message: 'Building Environment...', threshold: 20 },
      { message: 'Training Agents...', threshold: 40 },
      { message: 'Analyzing Market Data...', threshold: 60 },
      { message: 'Preparing Algorithms...', threshold: 80 },
      { message: 'Ready to Launch', threshold: 95 }
    ];
    
    // Simulate loading progress
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = Math.min(prev + Math.random() * 3, 100);
        
        // Update loading message based on progress thresholds
        const newMessage = loadingMessages.reduce((current, { message, threshold }) => {
          return newProgress >= threshold ? message : current;
        }, loadingMessage);
        
        if (newMessage !== loadingMessage) {
          setLoadingMessage(newMessage);
        }
        
        // Complete loading when progress reaches 100%
        if (newProgress >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            onLoadingComplete();
          }, 500);
        }
        
        return newProgress;
      });
    }, 100);
    
    return () => clearInterval(interval);
  }, [onLoadingComplete, loadingMessage]);
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #1a237e 0%, #283593 100%)',
      zIndex: 9999
    }}>
      <div style={{
        marginBottom: '40px',
        textAlign: 'center'
      }}>
        <h1 style={{
          fontSize: '3rem',
          color: 'white',
          margin: '0 0 10px 0',
          fontWeight: 'bold',
          textShadow: '0 2px 10px rgba(0,0,0,0.3)'
        }}>
          Welcome to Herkshire Bathaway
        </h1>
        
        <h2 style={{
          fontSize: '1.2rem',
          color: '#e3f2fd',
          fontWeight: 'normal',
          margin: '0',
          opacity: 0.8
        }}>
          Welcome to the future of algorithmic trading
        </h2>
      </div>
      
      {/* Loading bar container */}
      <div style={{
        width: '60%',
        maxWidth: '400px',
        height: '20px',
        backgroundColor: 'rgba(255,255,255,0.1)',
        borderRadius: '10px',
        overflow: 'hidden',
        position: 'relative',
        boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
      }}>
        {/* Progress bar */}
        <div style={{
          width: `${progress}%`,
          height: '100%',
          backgroundColor: '#64b5f6',
          borderRadius: '10px',
          transition: 'width 0.3s ease',
          boxShadow: '0 0 10px rgba(100, 181, 246, 0.7)',
          background: 'linear-gradient(90deg, #64b5f6 0%, #90caf9 100%)'
        }} />
        
        {/* Loading percentage text */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: 'white',
          fontSize: '12px',
          fontWeight: 'bold',
          textShadow: '0 1px 2px rgba(0,0,0,0.5)'
        }}>
          {Math.round(progress)}%
        </div>
      </div>
      
      {/* Loading message */}
      <div style={{
        marginTop: '20px',
        color: '#e3f2fd',
        fontSize: '1rem',
        fontWeight: 'bold',
        textShadow: '0 1px 3px rgba(0,0,0,0.3)',
        height: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {loadingMessage}
      </div>
      
      {/* Financial-themed low poly background elements */}
      <div style={{
        position: 'absolute',
        bottom: '10%',
        left: '5%',
        width: '90%',
        height: '30%',
        zIndex: -1,
        opacity: 0.2,
        background: 'url("data:image/svg+xml,%3Csvg width=\'100%25\' height=\'100%25\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M0,40 L20,35 L40,45 L60,40 L80,55 L100,30\' stroke=\'white\' stroke-width=\'2\' fill=\'none\'/%3E%3C/svg%3E") no-repeat bottom left',
        backgroundSize: 'cover'
      }} />
    </div>
  );
};

export default LoadingScreen;
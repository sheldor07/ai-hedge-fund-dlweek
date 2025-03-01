import React from 'react';
import { useDispatch } from 'react-redux';
import { setCurrentView } from '../store/simulationSlice';

const KnowledgeBaseButton: React.FC = () => {
  const dispatch = useDispatch();
  
  const handleOpenKnowledgeBase = () => {
    dispatch(setCurrentView('knowledgeBase'));
  };
  
  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 100,
      }}
    >
      <button
        onClick={handleOpenKnowledgeBase}
        style={{
          padding: '8px 15px',
          backgroundColor: '#4caf50',
          color: 'white',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
        }}
      >
        <span>📚</span>
        <span>Knowledge Base</span>
      </button>
    </div>
  );
};

export default KnowledgeBaseButton;
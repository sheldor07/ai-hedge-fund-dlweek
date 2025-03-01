import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import {
  startSimulation,
  pauseSimulation,
  setSimulationSpeed,
  setFocusedEntity,
} from '../store/simulationSlice';

const SimulationControls: React.FC = () => {
  const dispatch = useDispatch();
  const simulation = useSelector((state: RootState) => state.simulation);
  const focusedEntity = useSelector((state: RootState) => state.simulation.focusedEntity);

  const handleStartPause = () => {
    if (simulation.isRunning) {
      dispatch(pauseSimulation());
    } else {
      dispatch(startSimulation());
    }
  };

  const handleSpeedChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const speed = parseFloat(event.target.value);
    dispatch(setSimulationSpeed(speed));
  };

  const handleResetFocus = () => {
    dispatch(setFocusedEntity({ type: null, id: null }));
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        background: 'rgba(255, 255, 255, 0.8)',
        padding: '10px',
        borderRadius: '5px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        zIndex: 100,
      }}
    >
      <div>
        <button
          onClick={handleStartPause}
          style={{
            padding: '5px 10px',
            backgroundColor: simulation.isRunning ? '#f44336' : '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer',
            marginRight: '10px',
          }}
        >
          {simulation.isRunning ? 'Pause' : 'Start'}
        </button>
        
        {focusedEntity.id && (
          <button
            onClick={handleResetFocus}
            style={{
              padding: '5px 10px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              cursor: 'pointer',
            }}
          >
            Reset View
          </button>
        )}
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <span style={{ marginRight: '10px', fontSize: '14px' }}>Speed:</span>
        <input
          type="range"
          min="0.1"
          max="3"
          step="0.1"
          value={simulation.speed}
          onChange={handleSpeedChange}
          style={{ flex: 1 }}
        />
        <span style={{ marginLeft: '5px', fontSize: '14px' }}>{simulation.speed.toFixed(1)}x</span>
      </div>
      
      <div style={{ fontSize: '12px', color: '#555' }}>
        {focusedEntity.type && focusedEntity.id ? (
          <div>
            Focused on: {focusedEntity.type} {focusedEntity.id}
          </div>
        ) : (
          <div>Simulation Time: {formatTime(simulation.simulationTime)}</div>
        )}
      </div>
    </div>
  );
};

// Helper function to format simulation time
const formatTime = (ms: number): string => {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

export default SimulationControls;
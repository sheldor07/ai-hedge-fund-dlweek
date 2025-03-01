import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import {
  startSimulation,
  pauseSimulation,
  setSimulationSpeed,
  setFocusedEntity,
  fastForwardToNextDay,
  fastForwardToNextWeekday,
  DAILY_SCHEDULE
} from '../store/simulationSlice';
import { TimeOfDayPeriod } from '../models/types';

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

  const handleSpeedChange = (speed: number) => {
    dispatch(setSimulationSpeed(speed));
  };

  const handleResetFocus = () => {
    dispatch(setFocusedEntity({ type: null, id: null }));
  };

  const handleSkipToNextDay = () => {
    dispatch(fastForwardToNextDay());
  };

  const handleSkipToNextWeekday = () => {
    dispatch(fastForwardToNextWeekday());
  };

  // Format the current date and time
  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit'
    });
  };

  // Get the description for the current time period
  const getPeriodDescription = (periodType: TimeOfDayPeriod): string => {
    const period = DAILY_SCHEDULE.find(p => p.periodType === periodType);
    return period ? period.description : '';
  };

  // Get days remaining in simulation
  const getDaysRemaining = (): number => {
    const currentTime = simulation.currentDate.getTime();
    const endTime = simulation.simulationEndDate.getTime();
    return Math.ceil((endTime - currentTime) / (1000 * 60 * 60 * 24));
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        background: 'rgba(255, 255, 255, 0.9)',
        padding: '15px',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        zIndex: 100,
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        width: '300px',
      }}
    >
      {/* Date and Time Display */}
      <div style={{ 
        textAlign: 'center', 
        borderBottom: '1px solid #e0e0e0',
        paddingBottom: '8px',
        marginBottom: '8px'
      }}>
        <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#333' }}>
          {formatDate(simulation.currentDate)}
        </div>
        <div style={{ fontSize: '20px', color: '#1976d2', fontWeight: 'bold' }}>
          {formatTime(simulation.currentDate)}
        </div>
        <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
          {getPeriodDescription(simulation.currentTimeOfDay)}
        </div>
        <div style={{ fontSize: '12px', color: '#888', marginTop: '3px' }}>
          Day {Math.floor((simulation.currentDate.getTime() - simulation.simulationStartDate.getTime()) / (1000 * 60 * 60 * 24)) + 1} of 365 ({getDaysRemaining()} days remaining)
        </div>
      </div>

      {/* Playback Controls */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
        <button
          onClick={handleStartPause}
          style={{
            padding: '8px 15px',
            backgroundColor: simulation.isRunning ? '#f44336' : '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
            flex: 1,
          }}
        >
          {simulation.isRunning ? 'PAUSE' : 'PLAY'}
        </button>
        
        <button
          onClick={handleSkipToNextDay}
          style={{
            padding: '8px 15px',
            backgroundColor: '#ff9800',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            flex: 1,
          }}
          title="Skip to Next Day"
        >
          +1 Day
        </button>
        
        <button
          onClick={handleSkipToNextWeekday}
          style={{
            padding: '8px 15px',
            backgroundColor: '#ff5722',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            flex: 1,
          }}
          title="Skip to Next Weekday (Skip Weekends)"
        >
          +Weekend
        </button>
      </div>
      
      {/* Speed Controls */}
      <div>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          marginBottom: '5px'
        }}>
          <span style={{ fontSize: '14px', fontWeight: 'bold' }}>Simulation Speed:</span>
          <span style={{ 
            fontSize: '16px', 
            fontWeight: 'bold', 
            color: '#1976d2',
            backgroundColor: '#e3f2fd',
            padding: '3px 8px',
            borderRadius: '4px'
          }}>
            {simulation.speed}x
          </span>
        </div>
        
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          gap: '5px'
        }}>
          {simulation.speedOptions.map(speed => (
            <button
              key={speed}
              onClick={() => handleSpeedChange(speed)}
              style={{
                padding: '5px 0',
                backgroundColor: simulation.speed === speed ? '#2196f3' : '#e0e0e0',
                color: simulation.speed === speed ? 'white' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                flex: 1,
                fontWeight: simulation.speed === speed ? 'bold' : 'normal',
              }}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
      
      {/* Focus Controls */}
      {focusedEntity.id && (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={handleResetFocus}
            style={{
              padding: '8px 15px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              width: '100%',
            }}
          >
            Reset Camera View
          </button>
        </div>
      )}
      
      {/* Current Status */}
      <div style={{ 
        fontSize: '12px', 
        color: '#555', 
        backgroundColor: '#f5f5f5',
        padding: '8px',
        borderRadius: '4px',
        marginTop: '5px'
      }}>
        {focusedEntity.type && focusedEntity.id ? (
          <div>
            <span style={{ fontWeight: 'bold' }}>Focused on:</span> {focusedEntity.type} {focusedEntity.id}
          </div>
        ) : (
          <div>
            <span style={{ fontWeight: 'bold' }}>Status:</span> {simulation.isRunning ? 'Simulation running' : 'Simulation paused'}
          </div>
        )}
      </div>
    </div>
  );
};

export default SimulationControls;
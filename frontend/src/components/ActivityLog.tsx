import React, { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import {
  setCharacterTypeFilter,
  setRoomFilter,
  setActionTypeFilter,
  clearFilters,
  setAutoScroll,
  setShowDetailed,
  setSearchQuery,
  ActivityLogEntry,
} from '../store/activityLogSlice';
import { setFocusedEntity } from '../store/simulationSlice';

// Helper function to format timestamp
const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
};

const ActivityLog: React.FC = () => {
  const dispatch = useDispatch();
  const { entries, filter, autoScroll, showDetailed, searchQuery } = useSelector(
    (state: RootState) => state.activityLog
  );
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll behavior
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [entries, autoScroll]);

  // Filter entries
  const filteredEntries = entries.filter((entry) => {
    let matchesFilter = true;

    // Apply character type filter
    if (filter.characterType && !filter.characterType.includes(entry.characterType)) {
      matchesFilter = false;
    }

    // Apply room filter
    if (filter.roomId && entry.roomId !== filter.roomId) {
      matchesFilter = false;
    }

    // Apply action type filter
    if (filter.actionType && !filter.actionType.includes(entry.actionType)) {
      matchesFilter = false;
    }

    // Apply search query
    if (searchQuery && !entry.description.toLowerCase().includes(searchQuery.toLowerCase())) {
      matchesFilter = false;
    }

    return matchesFilter;
  });

  // Handlers
  const handleCharacterTypeFilterChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const value = event.target.value;
    if (value === 'all') {
      dispatch(setCharacterTypeFilter(null));
    } else {
      dispatch(setCharacterTypeFilter([value as any]));
    }
  };

  const handleActionTypeFilterChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const value = event.target.value;
    if (value === 'all') {
      dispatch(setActionTypeFilter(null));
    } else {
      dispatch(setActionTypeFilter([value as any]));
    }
  };

  const handleClearFilters = () => {
    dispatch(clearFilters());
    dispatch(setSearchQuery(''));
  };

  const handleAutoScrollChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setAutoScroll(event.target.checked));
  };

  const handleShowDetailedChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    dispatch(setShowDetailed(event.target.checked));
  };

  const handleSearchQueryChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    dispatch(setSearchQuery(event.target.value));
  };

  const handleCharacterClick = (characterId: string) => {
    dispatch(setFocusedEntity({ type: 'character', id: characterId }));
  };

  const handleRoomClick = (roomId: string) => {
    dispatch(setFocusedEntity({ type: 'room', id: roomId }));
  };

  // Render each log entry
  const renderLogEntry = (entry: ActivityLogEntry) => {
    const actionTypeColors: Record<string, string> = {
      movement: '#4287f5',
      analysis: '#42f54e',
      decision: '#f5a742',
      communication: '#f54242',
      trading: '#a142f5',
    };

    return (
      <div
        key={entry.id}
        className="activity-log-entry"
        style={{ borderLeft: `3px solid ${actionTypeColors[entry.actionType]}` }}
      >
        <div style={{ fontSize: '10px', color: '#777' }}>
          {formatTimestamp(entry.timestamp)}
        </div>
        <div>
          <span
            onClick={() => handleCharacterClick(entry.characterId)}
            style={{ fontWeight: 'bold', cursor: 'pointer', color: '#0066cc' }}
          >
            {entry.characterType}
          </span>{' '}
          in{' '}
          <span
            onClick={() => handleRoomClick(entry.roomId)}
            style={{ cursor: 'pointer', color: '#0066cc' }}
          >
            {entry.roomId}
          </span>
          :{' '}
          <span>{entry.description}</span>
        </div>
        {showDetailed && entry.details && (
          <pre style={{ fontSize: '10px', background: '#f5f5f5', padding: '4px' }}>
            {JSON.stringify(entry.details, null, 2)}
          </pre>
        )}
      </div>
    );
  };

  return (
    <div className="activity-log">
      <div className="activity-log-header">
        <strong>Activity Log</strong>
        <button onClick={handleClearFilters}>Clear Filters</button>
      </div>
      
      <div style={{ marginBottom: '10px' }}>
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={handleSearchQueryChange}
          style={{ width: '100%', padding: '4px', marginBottom: '5px' }}
        />
        
        <div style={{ display: 'flex', gap: '5px', marginBottom: '5px' }}>
          <select
            onChange={handleCharacterTypeFilterChange}
            value={filter.characterType ? filter.characterType[0] : 'all'}
            style={{ flex: 1 }}
          >
            <option value="all">All Characters</option>
            <option value="analyst">Analysts</option>
            <option value="quant">Quants</option>
            <option value="executive">Executives</option>
            <option value="riskManager">Risk Managers</option>
          </select>
          
          <select
            onChange={handleActionTypeFilterChange}
            value={filter.actionType ? filter.actionType[0] : 'all'}
            style={{ flex: 1 }}
          >
            <option value="all">All Actions</option>
            <option value="movement">Movement</option>
            <option value="analysis">Analysis</option>
            <option value="decision">Decision</option>
            <option value="communication">Communication</option>
            <option value="trading">Trading</option>
          </select>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', fontSize: '12px' }}>
          <label>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={handleAutoScrollChange}
            />
            Auto-scroll
          </label>
          <label>
            <input
              type="checkbox"
              checked={showDetailed}
              onChange={handleShowDetailedChange}
            />
            Show Details
          </label>
        </div>
      </div>
      
      <div
        ref={logContainerRef}
        style={{
          height: 'calc(100% - 120px)',
          overflowY: 'auto',
          padding: '5px',
        }}
      >
        {filteredEntries.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#777', marginTop: '20px' }}>
            No activities yet
          </div>
        ) : (
          filteredEntries.map(renderLogEntry)
        )}
      </div>
    </div>
  );
};

export default ActivityLog;
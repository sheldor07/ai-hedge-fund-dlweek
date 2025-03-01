import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setFocusedEntity } from '../store/simulationSlice';
import { Character } from '../store/charactersSlice';

// Task priority levels
type PriorityLevel = 'low' | 'medium' | 'high' | 'critical';

// Task status
type TaskStatus = 'queued' | 'in_progress' | 'completed';

// Research focus type
type ResearchType = 'technical' | 'fundamental';

// Mock task interface
interface Task {
  id: string;
  description: string;
  priority: PriorityLevel;
  estimatedCompletion: number; // timestamp
  status: TaskStatus;
  progress?: number; // 0-100
  assignedAgentId?: string;
  createdAt: number; // timestamp
  company?: string; // associated company ticker
}

// Mock research focus interface
interface ResearchFocus {
  companyId: string;
  ticker: string;
  type: ResearchType;
  metrics: string[];
  startTime: number;
  duration: number; // in milliseconds
  progress: number; // 0-100
}

// Generate a random integer between min and max (inclusive)
const getRandomInt = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

// Companies we're focusing on
const COMPANIES = [
  { id: 'amzn', ticker: 'AMZN', name: 'Amazon' },
  { id: 'nvda', ticker: 'NVDA', name: 'NVIDIA' },
  { id: 'mu', ticker: 'MU', name: 'Micron' },
  { id: 'wmt', ticker: 'WMT', name: 'Walmart' },
  { id: 'dis', ticker: 'DIS', name: 'Walt Disney' },
];

// Technical analysis metrics
const TECHNICAL_METRICS = [
  'Moving Averages',
  'RSI',
  'MACD',
  'Bollinger Bands',
  'Volume Analysis',
  'Support/Resistance',
  'Chart Patterns',
  'Trend Analysis',
  'Momentum Indicators',
  'Fibonacci Retracement',
];

// Fundamental analysis metrics
const FUNDAMENTAL_METRICS = [
  'P/E Ratio',
  'EPS Growth',
  'Revenue Trend',
  'Profit Margins',
  'Debt-to-Equity',
  'Cash Flow Analysis',
  'ROE',
  'Dividend Yield',
  'Industry Comparisons',
  'Management Changes',
];

// Generate mock tasks related to stock analysis
const generateMockTasks = (roomType: string, count: number): Task[] => {
  const tasks: Task[] = [];
  const now = Date.now();
  
  const isTechnical = roomType === 'technicalAnalysis';
  const taskTypes = isTechnical
    ? [
        'Analyze chart patterns for',
        'Calculate technical indicators for',
        'Evaluate trend strength for',
        'Assess price momentum for',
        'Compare volume patterns for',
        'Update technical models for',
        'Identify support/resistance for',
        'Backtest trading algorithm for',
        'Review volatility metrics for',
        'Check correlation analysis for',
      ]
    : [
        'Review quarterly earnings for',
        'Analyze balance sheet of',
        'Evaluate management team at',
        'Compare industry position of',
        'Calculate valuation metrics for',
        'Research market share of',
        'Examine cash flow trends of',
        'Assess growth prospects for',
        'Review debt structure of',
        'Analyze competitive advantage of',
      ];
  
  const priorities: PriorityLevel[] = ['low', 'medium', 'high', 'critical'];
  const statuses: TaskStatus[] = ['queued', 'in_progress', 'completed'];
  
  for (let i = 0; i < count; i++) {
    const company = COMPANIES[getRandomInt(0, COMPANIES.length - 1)];
    const priority = priorities[getRandomInt(0, priorities.length - 1)];
    const status = statuses[getRandomInt(0, statuses.length - 1)];
    const taskType = taskTypes[getRandomInt(0, taskTypes.length - 1)];
    
    const estimatedCompletionOffset = getRandomInt(1, 60) * 60 * 1000; // 1-60 minutes
    const createdAtOffset = getRandomInt(0, 120) * 60 * 1000; // 0-120 minutes ago
    
    const task: Task = {
      id: `task-${i}-${now}`,
      description: `${taskType} ${company.name}`,
      priority,
      estimatedCompletion: now + estimatedCompletionOffset,
      status,
      createdAt: now - createdAtOffset,
      company: company.ticker,
    };
    
    // Add progress for in-progress tasks
    if (status === 'in_progress') {
      task.progress = getRandomInt(10, 90);
    } else if (status === 'completed') {
      task.progress = 100;
    }
    
    tasks.push(task);
  }
  
  // Sort by priority and then by status (queued -> in_progress -> completed)
  return tasks.sort((a, b) => {
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    const statusOrder = { in_progress: 0, queued: 1, completed: 2 };
    
    const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
    if (priorityDiff !== 0) return priorityDiff;
    
    return statusOrder[a.status] - statusOrder[b.status];
  });
};

// Generate research focus for an agent
const generateResearchFocus = (roomType: string, character: Character): ResearchFocus | null => {
  // Not all agents have a research focus
  if (Math.random() > 0.7) return null;
  
  const company = COMPANIES[getRandomInt(0, COMPANIES.length - 1)];
  const now = Date.now();
  const isTechnical = roomType === 'technicalAnalysis';
  
  // Select metrics based on room type
  const metricsPool = isTechnical ? TECHNICAL_METRICS : FUNDAMENTAL_METRICS;
  const metricCount = getRandomInt(2, 5);
  const metrics: string[] = [];
  
  // Get random metrics without duplicates
  while (metrics.length < metricCount) {
    const metric = metricsPool[getRandomInt(0, metricsPool.length - 1)];
    if (!metrics.includes(metric)) {
      metrics.push(metric);
    }
  }
  
  return {
    companyId: company.id,
    ticker: company.ticker,
    type: isTechnical ? 'technical' : 'fundamental',
    metrics,
    startTime: now - getRandomInt(1, 30) * 60 * 1000, // 1-30 minutes ago
    duration: getRandomInt(30, 120) * 60 * 1000, // 30-120 minutes
    progress: getRandomInt(10, 95), // 10-95% progress
  };
};

// Format time duration in a human-readable format
const formatDuration = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000);
  
  if (seconds < 60) {
    return `${seconds}s`;
  }
  
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
};

// Format time until completion
const formatTimeUntil = (timestamp: number): string => {
  const now = Date.now();
  const remainingTime = timestamp - now;
  
  if (remainingTime <= 0) {
    return 'now';
  }
  
  return formatDuration(remainingTime);
};

// Get color for priority level
const getPriorityColor = (priority: PriorityLevel): string => {
  switch (priority) {
    case 'critical': return '#f44336'; // Red
    case 'high': return '#ff9800'; // Orange
    case 'medium': return '#2196f3'; // Blue
    case 'low': return '#4caf50'; // Green
    default: return '#9e9e9e'; // Grey
  }
};

// Get color for agent type
const getAgentColor = (type: string): string => {
  const colors: Record<string, string> = {
    analyst: '#1976d2', // Blue
    quant: '#2e7d32', // Green
    executive: '#e65100', // Orange
    riskManager: '#d32f2f', // Red
  };
  
  return colors[type] || '#9e9e9e';
};

// Get color for research type
const getResearchTypeColor = (type: ResearchType): string => {
  return type === 'technical' ? '#2e7d32' : '#1976d2';
};

// Format priority label with icon
const PriorityLabel: React.FC<{ priority: PriorityLevel }> = ({ priority }) => {
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      color: getPriorityColor(priority),
      fontWeight: 'bold',
      fontSize: '0.8rem',
    }}>
      {priority === 'critical' && '🔥 '}
      {priority === 'high' && '⚠️ '}
      {priority === 'medium' && '📋 '}
      {priority === 'low' && '📝 '}
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </div>
  );
};

// Format status label with icon
const StatusLabel: React.FC<{ status: TaskStatus }> = ({ status }) => {
  let color = '#9e9e9e';
  let icon = '';
  
  switch (status) {
    case 'in_progress':
      color = '#2196f3';
      icon = '⏳ ';
      break;
    case 'queued':
      color = '#ff9800';
      icon = '⌛ ';
      break;
    case 'completed':
      color = '#4caf50';
      icon = '✅ ';
      break;
  }
  
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      color,
      fontWeight: 'bold',
      fontSize: '0.8rem',
    }}>
      {icon}
      {status === 'in_progress' ? 'In Progress' : status.charAt(0).toUpperCase() + status.slice(1)}
    </div>
  );
};

// Task item component
const TaskItem: React.FC<{ task: Task }> = ({ task }) => {
  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.8)',
      borderRadius: '8px',
      padding: '12px',
      marginBottom: '10px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      borderLeft: `4px solid ${getPriorityColor(task.priority)}`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ fontWeight: 'bold' }}>{task.description}</div>
        <div>
          {task.company && (
            <span style={{ 
              background: '#e0e0e0',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '0.8rem',
              fontWeight: 'bold',
            }}>
              {task.company}
            </span>
          )}
        </div>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
        <PriorityLabel priority={task.priority} />
        <StatusLabel status={task.status} />
      </div>
      
      {task.status === 'in_progress' && task.progress !== undefined && (
        <div style={{ marginTop: '8px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '4px',
            fontSize: '0.8rem',
          }}>
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div style={{ 
            width: '100%', 
            height: '6px', 
            background: '#e0e0e0',
            borderRadius: '3px',
            overflow: 'hidden',
          }}>
            <div style={{ 
              width: `${task.progress}%`, 
              height: '100%', 
              background: '#2196f3',
              borderRadius: '3px',
            }} />
          </div>
        </div>
      )}
      
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        marginTop: '8px',
        fontSize: '0.8rem',
        color: '#757575',
      }}>
        <div>
          Created: {new Date(task.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
        <div>
          {task.status === 'completed' 
            ? 'Completed' 
            : `Est: ${formatTimeUntil(task.estimatedCompletion)}`}
        </div>
      </div>
    </div>
  );
};

// Agent card component
const AgentCard: React.FC<{ 
  character: Character; 
  roomType: string;
  onClick: () => void;
  isSelected: boolean;
}> = ({ character, roomType, onClick, isSelected }) => {
  const [researchFocus, setResearchFocus] = useState<ResearchFocus | null>(null);
  
  useEffect(() => {
    setResearchFocus(generateResearchFocus(roomType, character));
  }, [character, roomType]);
  
  return (
    <div 
      style={{
        background: isSelected ? 'rgba(255, 255, 255, 0.9)' : 'rgba(255, 255, 255, 0.7)',
        borderRadius: '10px',
        padding: '15px',
        marginBottom: '15px',
        boxShadow: isSelected ? '0 4px 10px rgba(0,0,0,0.15)' : '0 2px 5px rgba(0,0,0,0.1)',
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        border: isSelected ? `2px solid ${getAgentColor(character.type)}` : '2px solid transparent',
      }}
      onClick={onClick}
    >
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: getAgentColor(character.type),
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: '1.2rem',
          marginRight: '15px',
        }}>
          {character.name.charAt(0)}
        </div>
        
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>{character.name}</div>
          <div style={{ fontSize: '0.9rem', color: '#757575' }}>
            {character.type.charAt(0).toUpperCase() + character.type.slice(1)}
          </div>
        </div>
        
        <div style={{
          marginLeft: 'auto',
          padding: '4px 8px',
          borderRadius: '12px',
          fontSize: '0.8rem',
          fontWeight: 'bold',
          color: 'white',
          background: character.state === 'idle' 
            ? '#9e9e9e' 
            : character.state === 'working' 
              ? '#4caf50'
              : character.state === 'talking'
                ? '#2196f3'
                : '#ff9800',
        }}>
          {character.state.charAt(0).toUpperCase() + character.state.slice(1)}
        </div>
      </div>
      
      {character.currentTask && (
        <div style={{ 
          marginTop: '10px',
          padding: '8px',
          background: 'rgba(0, 0, 0, 0.05)',
          borderRadius: '5px',
          fontSize: '0.9rem',
          fontStyle: 'italic'
        }}>
          "{character.currentTask}"
        </div>
      )}
      
      {researchFocus && (
        <div style={{
          marginTop: '10px',
          display: 'flex',
          alignItems: 'center',
          fontSize: '0.85rem',
        }}>
          <div style={{
            padding: '2px 6px',
            borderRadius: '4px',
            background: getResearchTypeColor(researchFocus.type),
            color: 'white',
            fontWeight: 'bold',
            marginRight: '8px',
            fontSize: '0.75rem',
          }}>
            {researchFocus.type === 'technical' ? 'Technical' : 'Fundamental'}
          </div>
          <div style={{ fontWeight: 'bold' }}>
            Researching {researchFocus.ticker}
          </div>
        </div>
      )}
    </div>
  );
};

// Research visualization component
const ResearchVisualization: React.FC<{ 
  researchFocus: ResearchFocus | null;
  roomType: string;
}> = ({ researchFocus, roomType }) => {
  if (!researchFocus) {
    return (
      <div style={{
        background: 'rgba(255, 255, 255, 0.8)',
        borderRadius: '10px',
        padding: '20px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '200px',
        fontSize: '0.9rem',
        color: '#757575',
        textAlign: 'center',
      }}>
        No active research session.<br />
        Select an agent with research focus to view details.
      </div>
    );
  }
  
  // Find the company details
  const company = COMPANIES.find(c => c.id === researchFocus.companyId) || COMPANIES[0];
  
  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.8)',
      borderRadius: '10px',
      padding: '20px',
      zIndex: 100,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '15px',
      }}>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{company.name} ({company.ticker})</div>
          <div style={{ fontSize: '0.9rem', color: '#757575' }}>
            {researchFocus.type === 'technical' ? 'Technical Analysis' : 'Fundamental Analysis'}
          </div>
        </div>
        
        <div style={{
          background: getResearchTypeColor(researchFocus.type),
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: '1.2rem',
        }}>
          {company.ticker.charAt(0)}
        </div>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '4px',
          fontSize: '0.9rem',
        }}>
          <span>Research Progress</span>
          <span>{researchFocus.progress}%</span>
        </div>
        <div style={{ 
          width: '100%', 
          height: '8px', 
          background: '#e0e0e0',
          borderRadius: '4px',
          overflow: 'hidden',
        }}>
          <div style={{ 
            width: `${researchFocus.progress}%`, 
            height: '100%', 
            background: getResearchTypeColor(researchFocus.type),
            borderRadius: '4px',
          }} />
        </div>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginTop: '4px',
          fontSize: '0.8rem',
          color: '#757575',
        }}>
          <div>Started {formatDuration(Date.now() - researchFocus.startTime)} ago</div>
          <div>Est. completion: {formatDuration(researchFocus.duration * (1 - researchFocus.progress / 100))}</div>
        </div>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '8px' }}>
          Analyzing Metrics:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {researchFocus.metrics.map((metric, index) => (
            <div key={index} style={{
              padding: '5px 10px',
              background: '#f5f5f5',
              borderRadius: '15px',
              fontSize: '0.8rem',
              border: `1px solid ${getResearchTypeColor(researchFocus.type)}`,
            }}>
              {metric}
            </div>
          ))}
        </div>
      </div>
      
      {/* Visualization graph */}
      <div style={{ marginTop: '15px', height: '100px', position: 'relative' }}>
        {roomType === 'technicalAnalysis' ? (
          <>
            {/* Mock technical chart */}
            <svg width="100%" height="100%" viewBox="0 0 300 100" preserveAspectRatio="none">
              <path
                d="M0,70 C20,60 40,80 60,40 C80,0 100,20 120,30 C140,40 160,10 180,50 C200,90 220,60 240,70 C260,80 280,50 300,60"
                fill="none"
                stroke={getResearchTypeColor('technical')}
                strokeWidth="2"
              />
              <path
                d="M0,70 C20,60 40,80 60,40 C80,0 100,20 120,30 C140,40 160,10 180,50 C200,90 220,60 240,70 C260,80 280,50 300,60"
                fill={`${getResearchTypeColor('technical')}20`}
                strokeWidth="0"
                transform="translate(0, 20)"
              />
            </svg>
            
            {/* Chart labels */}
            <div style={{ 
              position: 'absolute', 
              top: 0, 
              left: 0,
              fontSize: '0.7rem',
              color: '#757575',
            }}>
              ${getRandomInt(100, 500).toFixed(2)}
            </div>
            <div style={{ 
              position: 'absolute', 
              bottom: 0, 
              left: 0,
              fontSize: '0.7rem',
              color: '#757575',
            }}>
              ${getRandomInt(50, 90).toFixed(2)}
            </div>
          </>
        ) : (
          <>
            {/* Mock fundamental chart (bar chart) */}
            <svg width="100%" height="100%" viewBox="0 0 300 100" preserveAspectRatio="none">
              <rect x="20" y="20" width="30" height="80" fill={`${getResearchTypeColor('fundamental')}90`} />
              <rect x="60" y="50" width="30" height="50" fill={`${getResearchTypeColor('fundamental')}90`} />
              <rect x="100" y="30" width="30" height="70" fill={`${getResearchTypeColor('fundamental')}90`} />
              <rect x="140" y="10" width="30" height="90" fill={`${getResearchTypeColor('fundamental')}90`} />
              <rect x="180" y="40" width="30" height="60" fill={`${getResearchTypeColor('fundamental')}90`} />
              <rect x="220" y="60" width="30" height="40" fill={`${getResearchTypeColor('fundamental')}90`} />
              <rect x="260" y="25" width="30" height="75" fill={`${getResearchTypeColor('fundamental')}90`} />
            </svg>
            
            {/* Chart labels */}
            <div style={{ 
              position: 'absolute', 
              top: 0, 
              left: 0,
              fontSize: '0.7rem',
              color: '#757575',
            }}>
              100%
            </div>
            <div style={{ 
              position: 'absolute', 
              bottom: 0, 
              left: 0,
              fontSize: '0.7rem',
              color: '#757575',
            }}>
              0%
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// Main AgentViewPanel component
const AgentViewPanel: React.FC = () => {
  const dispatch = useDispatch();
  const focusedEntity = useSelector((state: RootState) => state.simulation.focusedEntity);
  const characters = useSelector((state: RootState) => state.characters.characters);
  
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);
  const [animationClass, setAnimationClass] = useState('');
  const [filteredTaskStatus, setFilteredTaskStatus] = useState<TaskStatus | 'all'>('all');
  
  // Find the currently selected room
  const roomId = focusedEntity.type === 'room' ? focusedEntity.id : null;
  
  // Get the room type based on room ID (hacky but works for our example)
  let roomType = '';
  if (roomId === 'room-0') roomType = 'fundamentalAnalysis';
  if (roomId === 'room-1') roomType = 'technicalAnalysis';
  if (roomId === 'room-2') roomType = 'executiveSuite';
  if (roomId === 'room-3') roomType = 'tradingFloor';
  
  // Get the room name
  let roomName = '';
  if (roomType === 'fundamentalAnalysis') roomName = 'Fundamental Analysis';
  if (roomType === 'technicalAnalysis') roomName = 'Technical Analysis';
  if (roomType === 'executiveSuite') roomName = 'Executive Suite';
  if (roomType === 'tradingFloor') roomName = 'Trading Floor';
  
  // Filter characters that are in this room
  const roomCharacters = characters.filter(character => character.currentRoom === roomId);
  
  // Find selected character
  const selectedCharacter = selectedCharacterId
    ? roomCharacters.find(character => character.id === selectedCharacterId)
    : null;
  
  // Find research focus for selected character
  const [researchFocus, setResearchFocus] = useState<ResearchFocus | null>(null);
  
  // Initialize and update tasks
  useEffect(() => {
    if (!roomId) return;
    
    setAnimationClass('slide-in');
    
    // Generate initial tasks
    setTasks(generateMockTasks(roomType, 12));
    
    // Update tasks periodically
    const taskInterval = setInterval(() => {
      setTasks(prevTasks => {
        // Randomly update the status of some tasks
        return prevTasks.map(task => {
          if (task.status === 'in_progress' && Math.random() < 0.3) {
            // Update progress or mark as completed
            if (task.progress && task.progress >= 90) {
              return { ...task, status: 'completed', progress: 100 };
            } else {
              return { ...task, progress: (task.progress || 0) + getRandomInt(5, 15) };
            }
          } else if (task.status === 'queued' && Math.random() < 0.2) {
            // Start queued task
            return { ...task, status: 'in_progress', progress: getRandomInt(5, 15) };
          }
          return task;
        });
      });
    }, 5000);
    
    // Add new task occasionally
    const newTaskInterval = setInterval(() => {
      if (Math.random() < 0.3) {
        setTasks(prevTasks => {
          const newTask = generateMockTasks(roomType, 1)[0];
          return [newTask, ...prevTasks.slice(0, -1)]; // Add to beginning, remove last
        });
      }
    }, 8000);
    
    return () => {
      clearInterval(taskInterval);
      clearInterval(newTaskInterval);
    };
  }, [roomId, roomType]);
  
  // Update research focus when selected character changes
  useEffect(() => {
    if (selectedCharacter) {
      setResearchFocus(generateResearchFocus(roomType, selectedCharacter));
    } else {
      setResearchFocus(null);
    }
  }, [selectedCharacter, roomType]);
  
  // If no room is selected, don't render anything
  if (!roomId) {
    return null;
  }
  
  // Handle close panel
  const handleClose = () => {
    setAnimationClass('slide-out');
    setTimeout(() => {
      dispatch(setFocusedEntity({ type: null, id: null }));
    }, 300);
  };
  
  // Handle agent selection
  const handleSelectAgent = (characterId: string) => {
    setSelectedCharacterId(prev => prev === characterId ? null : characterId);
  };
  
  // Filter tasks based on filter state
  const filteredTasks = filteredTaskStatus === 'all'
    ? tasks
    : tasks.filter(task => task.status === filteredTaskStatus);
  
  // Get a count of tasks by status
  const taskCounts = tasks.reduce((acc, task) => {
    acc[task.status] = (acc[task.status] || 0) + 1;
    return acc;
  }, {} as Record<TaskStatus, number>);
  
  return (
    <div className={`agent-view-panel ${animationClass}`} style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '30%',
      height: '100vh',
      backgroundColor: 'rgba(38, 50, 56, 0.95)',
      boxShadow: '-5px 0 15px rgba(0, 0, 0, 0.2)',
      zIndex: 1000,
      padding: '20px',
      overflowY: 'auto',
      color: '#fff',
      transition: 'transform 0.3s ease-in-out',
      transform: animationClass === 'slide-out' ? 'translateX(100%)' : 'translateX(0)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
        paddingBottom: '15px',
      }}>
        <div>
          <h2 style={{ margin: '0 0 5px 0', fontSize: '1.5rem' }}>{roomName}</h2>
          <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.9rem' }}>
            {roomCharacters.length} agent{roomCharacters.length !== 1 ? 's' : ''} working in this room
          </p>
        </div>
        
        <button
          onClick={handleClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            fontSize: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            transition: 'background-color 0.2s',
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
          ✕
        </button>
      </div>
      
      {/* Agent Overview Section */}
      <div style={{ marginBottom: '25px' }}>
        <h3 style={{ 
          margin: '0 0 15px 0', 
          fontSize: '1.1rem',
          display: 'flex',
          alignItems: 'center',
        }}>
          <span style={{ 
            width: '18px', 
            height: '18px', 
            background: '#4caf50',
            borderRadius: '50%',
            display: 'inline-block',
            marginRight: '10px',
          }}></span>
          Agent Overview
        </h3>
        
        {roomCharacters.length === 0 ? (
          <div style={{ 
            padding: '15px', 
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            textAlign: 'center',
            fontSize: '0.9rem',
          }}>
            No agents currently in this room
          </div>
        ) : (
          <div>
            {roomCharacters.map(character => (
              <AgentCard
                key={character.id}
                character={character}
                roomType={roomType}
                onClick={() => handleSelectAgent(character.id)}
                isSelected={selectedCharacterId === character.id}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Research Focus Section */}
      <div style={{ marginBottom: '25px' }}>
        <h3 style={{ 
          margin: '0 0 15px 0', 
          fontSize: '1.1rem',
          display: 'flex',
          alignItems: 'center',
        }}>
          <span style={{ 
            width: '18px', 
            height: '18px', 
            background: '#2196f3',
            borderRadius: '50%',
            display: 'inline-block',
            marginRight: '10px',
          }}></span>
          Research Focus
        </h3>
        
        <ResearchVisualization 
          researchFocus={researchFocus} 
          roomType={roomType}
        />
      </div>
      
      {/* Task Queue Section */}
      <div>
        <h3 style={{ 
          margin: '0 0 15px 0', 
          fontSize: '1.1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ 
              width: '18px', 
              height: '18px', 
              background: '#ff9800',
              borderRadius: '50%',
              display: 'inline-block',
              marginRight: '10px',
            }}></span>
            Task Queue
          </div>
          
          <div style={{ fontSize: '0.8rem' }}>
            {Object.entries(taskCounts).map(([status, count]) => (
              <span 
                key={status} 
                style={{ 
                  marginLeft: '10px',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  background: filteredTaskStatus === status
                    ? status === 'in_progress'
                      ? '#2196f3'
                      : status === 'queued'
                        ? '#ff9800'
                        : status === 'completed'
                          ? '#4caf50'
                          : 'rgba(255, 255, 255, 0.2)'
                    : 'rgba(255, 255, 255, 0.1)',
                  cursor: 'pointer',
                }}
                onClick={() => setFilteredTaskStatus(
                  filteredTaskStatus === status as TaskStatus ? 'all' : status as TaskStatus
                )}
              >
                {status === 'in_progress' ? 'In Progress' : status.charAt(0).toUpperCase() + status.slice(1)}: {count}
              </span>
            ))}
          </div>
        </h3>
        
        <div style={{ 
          maxHeight: '300px', 
          overflowY: 'auto',
          paddingRight: '10px',
        }}>
          {filteredTasks.length === 0 ? (
            <div style={{ 
              padding: '15px', 
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              textAlign: 'center',
              fontSize: '0.9rem',
            }}>
              No tasks match the current filter
            </div>
          ) : (
            filteredTasks.map(task => (
              <TaskItem key={task.id} task={task} />
            ))
          )}
        </div>
      </div>
      
      {/* Add CSS for animation */}
      <style>{`
        .slide-in {
          animation: slideIn 0.3s forwards;
        }
        
        .slide-out {
          animation: slideOut 0.3s forwards;
        }
        
        @keyframes slideIn {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
        
        @keyframes slideOut {
          from {
            transform: translateX(0);
          }
          to {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
};

export default AgentViewPanel;
import { useEffect, useCallback, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/index';
import { 
  updateSimulationTime, 
  updateDayNightCycle,
  updateCurrentDate,
  addPerformanceMetric,
  addMarketEvent,
  removeMarketEvent,
  addCharacterEvent,
  activateCharacterEvent,
  completeCharacterEvent,
  PerformanceMetric,
  DAILY_SCHEDULE,
  pauseSimulation
} from '../store/simulationSlice';
import { 
  CharacterEvent, 
  EventType, 
  TimeOfDayPeriod,
  CharacterType,
  CharacterState,
  DayType
} from '../models/types';
import { 
  addCharacter, 
  setCharacterTarget, 
  updateCharacterState,
  updateCharacterTask,
  addConversation,
  addActivityToHistory,
  Character,
  updateCharacterRoom,
  Position,
  Target
} from '../store/charactersSlice';
import { addLogEntry } from '../store/activityLogSlice';
import { 
  loadSimulatedEvents, 
  getEventsForTimestamp, 
  mapToMarketEvent, 
  mapToActivityLogEntry,
  SimulatedEvent,
  SimulatedEventsData
} from '../utils/simulationEventLoader';

// Array of first names for random character generation
const FIRST_NAMES = [
  'Alex', 'Blake', 'Casey', 'Dana', 'Ellis', 'Francis', 'Gray', 'Harper',
  'Indigo', 'Jordan', 'Kelly', 'Logan', 'Morgan', 'Noah', 'Olivia', 'Parker',
  'Quinn', 'Riley', 'Sam', 'Taylor', 'Uma', 'Val', 'Winter', 'Xavier'
];

// Array of last names for random character generation
const LAST_NAMES = [
  'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson',
  'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson',
  'Garcia', 'Martinez', 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee', 'Walker'
];

// Fixed room positions
const ROOM_POSITIONS = {
  'room-0': { x: -8, y: 0, z: -8 }, // Fundamental Analysis
  'room-1': { x: 8, y: 0, z: -8 },  // Technical Analysis
  'room-2': { x: -8, y: 0, z: 8 },  // Executive Suite
  'room-3': { x: 8, y: 0, z: 8 },   // Trading Floor
};

// Market event types for simulation
const MARKET_EVENT_TYPES = [
  { type: 'Earnings Report', impacts: ['positive', 'negative'] },
  { type: 'Fed Rate Decision', impacts: ['positive', 'negative', 'neutral'] },
  { type: 'Economic Data Release', impacts: ['positive', 'negative', 'neutral'] },
  { type: 'Geopolitical Event', impacts: ['negative', 'neutral'] },
  { type: 'Company Merger', impacts: ['positive'] },
  { type: 'Market Selloff', impacts: ['negative'] },
  { type: 'Sector Rotation', impacts: ['neutral'] },
  { type: 'Technical Breakout', impacts: ['positive'] },
  { type: 'Liquidity Crisis', impacts: ['negative'] },
  { type: 'New Regulations', impacts: ['negative', 'neutral'] },
];

// Character decision-making messages
const CHARACTER_MESSAGES = {
  analyst: [
    'Analyzing recent quarterly reports...',
    'Checking industry trends...',
    'Comparing balance sheet metrics...',
    'Reviewing management changes...',
    'Evaluating competitor performance...',
  ],
  quant: [
    'Running regression analysis...',
    'Optimizing trading algorithm...',
    'Backtesting new strategy...',
    'Examining correlation factors...',
    'Calculating volatility metrics...',
  ],
  executive: [
    'Reviewing overall fund performance...',
    'Evaluating risk exposure levels...',
    'Planning capital allocation...',
    'Assessing market opportunities...',
    'Setting investment strategy...',
  ],
  riskManager: [
    'Monitoring position limits...',
    'Assessing VaR metrics...',
    'Evaluating counterparty risk...',
    'Stress testing portfolios...',
    'Reviewing compliance standards...',
  ],
};

// Character conversations for interaction
const CONVERSATIONS = [
  'Did you see the latest market movement?',
  'I\'m seeing an interesting pattern in these numbers.',
  'We should adjust our exposure to this sector.',
  'The fundamentals are strong but technicals suggest caution.',
  'Let\'s discuss this at the next strategy meeting.',
  'Our model indicates a potential opportunity here.',
  'We need to hedge this position better.',
  'The risk metrics are showing some concerns.',
  'I think we should increase our allocation here.',
  'This volatility is creating some good entry points.',
];

// Generate a random position within a room
const getRandomPositionInRoom = (roomId: string): Position => {
  const basePosition = ROOM_POSITIONS[roomId as keyof typeof ROOM_POSITIONS];
  
  return {
    x: basePosition.x + (Math.random() * 4 - 2),
    y: 0,
    z: basePosition.z + (Math.random() * 4 - 2),
  };
};

// Generate a random name
const getRandomName = (): string => {
  const firstName = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
  const lastName = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
  return `${firstName} ${lastName}`;
};

// Generate random skill values that sum to approximately 1
const generateRandomSkills = (type: CharacterType) => {
  // Base values for each character type emphasizing their primary role
  let skills = {
    analysis: 0.2,
    decision: 0.2,
    communication: 0.2,
    risk: 0.2,
  };
  
  // Adjust based on character type
  switch (type) {
    case 'analyst':
      skills.analysis += 0.2;
      break;
    case 'quant':
      skills.analysis += 0.1;
      skills.decision += 0.1;
      break;
    case 'executive':
      skills.decision += 0.1;
      skills.communication += 0.1;
      break;
    case 'riskManager':
      skills.risk += 0.2;
      break;
  }
  
  // Add some randomness
  for (const key in skills) {
    if (Object.prototype.hasOwnProperty.call(skills, key)) {
      // @ts-ignore - TypeScript doesn't know we're iterating over the keys of skills
      skills[key] += Math.random() * 0.1;
    }
  }
  
  return skills;
};

// Stock symbols for event generation
const STOCKS = ['AMZN', 'NVDA', 'MU', 'WMT', 'DIS'];

// Event content templates for different event types
const EVENT_TEMPLATES: Record<TimeOfDayPeriod, Array<{ message: string; priority: number }>> = {
  MORNING_BRIEFING: [
    { message: "Today we need to watch {stock} closely. Earnings report is expected after market close.", priority: 3 },
    { message: "I've prepared a fundamental analysis of {stock}'s last quarter performance.", priority: 2 },
    { message: "Technical indicators for {stock} suggest possible volatility ahead.", priority: 2 },
    { message: "The market is expecting strong guidance from {stock} today.", priority: 2 },
    { message: "Our exposure to {stock} is currently at {num}%. Should we adjust?", priority: 3 },
  ],
  ANALYSIS_PHASE: [
    { message: "{stock} is showing a bullish divergence on the 4-hour chart.", priority: 2 },
    { message: "The inventory turnover for {stock} has improved by {num}% this quarter.", priority: 2 },
    { message: "I've completed my analysis of {stock}'s balance sheet.", priority: 1 },
    { message: "The competitive landscape for {stock} has changed significantly.", priority: 2 },
    { message: "We should consider the impact of new regulations on {stock}.", priority: 2 },
  ],
  LUNCH_BREAK: [
    { message: "Taking a quick lunch break while monitoring {stock}'s performance.", priority: 1 },
    { message: "Reviewing {stock}'s morning activity over lunch.", priority: 1 },
    { message: "Discussing {stock}'s market position with colleagues during lunch.", priority: 2 },
  ],
  STRATEGY_MEETING: [
    { message: "Our models indicate {stock} is undervalued by approximately {num}%.", priority: 3 },
    { message: "The correlation between {stock} and the sector index has weakened.", priority: 2 },
    { message: "I propose we adjust our position sizing for {stock}.", priority: 3 },
    { message: "The risk-reward ratio for {stock} has improved this week.", priority: 2 },
    { message: "We need a hedging strategy for our {stock} position.", priority: 3 },
  ],
  TRADE_EXECUTION: [
    { message: "Based on the analysis, let's increase our position in {stock} by {num}%.", priority: 4 },
    { message: "Algorithm suggests reducing exposure to {stock} due to sector headwinds.", priority: 4 },
    { message: "Initiating buy order for {stock} at market price.", priority: 4 },
    { message: "Setting up a stop-loss for {stock} at {num} points below current price.", priority: 3 },
  ],
  END_OF_DAY_REVIEW: [
    { message: "Reviewing today's performance for {stock}.", priority: 2 },
    { message: "Preparing end-of-day report on {stock} positions.", priority: 2 },
    { message: "Analyzing {stock}'s closing price action.", priority: 2 },
    { message: "Documenting key {stock} developments for tomorrow.", priority: 2 },
  ],
  AFTER_HOURS: [
    { message: "Monitoring after-hours trading activity for {stock}.", priority: 1 },
    { message: "Reviewing international market impact on {stock}.", priority: 1 },
    { message: "Preparing overnight analysis for {stock}.", priority: 1 },
  ]
};

// Function to generate a random character event based on the time of day
const generateRandomEvent = (
  currentDate: Date, 
  characters: any[], 
  timeOfDay: TimeOfDayPeriod
): CharacterEvent | null => {
  // Don't generate events for after hours
  if (timeOfDay === 'AFTER_HOURS') {
    return null;
  }
  
  // Get characters that aren't busy
  const availableCharacters = characters.filter(char => 
    char.state !== 'walking' && char.state !== 'talking'
  );
  
  if (availableCharacters.length === 0) {
    return null;
  }
  
  // Select random characters for the event
  const mainCharacter = availableCharacters[Math.floor(Math.random() * availableCharacters.length)];
  
  // Determine event type based on time of day and character type
  let eventType: EventType;
  
  switch (timeOfDay) {
    case 'MORNING_BRIEFING':
      eventType = Math.random() > 0.3 ? 'DISCUSS' : 'ANALYZE';
      break;
    case 'ANALYSIS_PHASE':
      eventType = Math.random() > 0.7 ? 'DISCUSS' : 'ANALYZE';
      break;
    case 'LUNCH_BREAK':
      eventType = 'MOVE';
      break;
    case 'STRATEGY_MEETING':
      eventType = Math.random() > 0.2 ? 'DISCUSS' : 'ANALYZE';
      break;
    case 'TRADE_EXECUTION':
      eventType = Math.random() > 0.5 ? 'DECIDE' : 'ANALYZE';
      break;
    case 'END_OF_DAY_REVIEW':
      eventType = Math.random() > 0.3 ? 'DISCUSS' : 'DECIDE';
      break;
    default:
      eventType = 'MOVE';
  }
  
  // Get participant IDs
  const characterIds = [mainCharacter.id];
  
  // For discussion events, add a second character
  if (eventType === 'DISCUSS' && availableCharacters.length > 1) {
    const otherAvailableCharacters = availableCharacters.filter(char => char.id !== mainCharacter.id);
    if (otherAvailableCharacters.length > 0) {
      const secondCharacter = otherAvailableCharacters[Math.floor(Math.random() * otherAvailableCharacters.length)];
      characterIds.push(secondCharacter.id);
    }
  }
  
  // Select a random stock
  const stock = STOCKS[Math.floor(Math.random() * STOCKS.length)];
  
  // Generate message based on time of day and event type
  let message = '';
  let priority = 1;
  
  if (EVENT_TEMPLATES[timeOfDay]) {
    const template = EVENT_TEMPLATES[timeOfDay][Math.floor(Math.random() * EVENT_TEMPLATES[timeOfDay].length)];
    message = template.message
      .replace('{stock}', stock)
      .replace('{num}', (Math.floor(Math.random() * 20) + 1).toString());
    priority = template.priority;
  } else {
    message = `Discussing ${stock} performance`;
  }
  
  // Set event duration based on type
  let duration = 0;
  switch (eventType) {
    case 'MOVE':
      duration = 5000 + Math.random() * 5000;
      break;
    case 'ANALYZE':
      duration = 10000 + Math.random() * 20000;
      break;
    case 'DISCUSS':
      duration = 8000 + Math.random() * 12000;
      break;
    case 'DECIDE':
      duration = 5000 + Math.random() * 10000;
      break;
  }
  
  // Create the event
  return {
    id: `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(currentDate),
    characterIds,
    originRoom: mainCharacter.currentRoom,
    eventType,
    message,
    duration,
    relatedStock: stock,
    priority,
    completed: false
  };
};

// Hook for simulation engine
// Event to notify the app when a day is complete
export const onDayComplete = new EventTarget();

const useSimulationEngine = () => {
  const dispatch = useDispatch();
  const { 
    isRunning, 
    speed, 
    simulationTime, 
    currentMarketEvents,
    currentDate,
    simulationStartDate,
    simulationEndDate,
    currentTimeOfDay,
    pendingCharacterEvents,
    activeCharacterEvents,
    dayType
  } = useSelector((state: RootState) => state.simulation);
  
  const characters = useSelector((state: RootState) => state.characters.characters);
  
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  const [lastEventGenerationTime, setLastEventGenerationTime] = useState(0);
  const lastDateRef = useRef<Date | null>(null);
  
  // Initialize simulation with characters
  const initializeSimulation = useCallback(() => {
    // Create characters for each role
    const characterTypes: CharacterType[] = ['analyst', 'quant', 'executive', 'riskManager'];
    
    characterTypes.forEach((type, index) => {
      // Create multiple characters of each type
      const count = type === 'executive' ? 1 : 3; // Fewer executives
      
      for (let i = 0; i < count; i++) {
        // Determine initial room based on character type
        let roomId = '';
        switch (type) {
          case 'analyst':
            roomId = 'room-0'; // Fundamental Analysis
            break;
          case 'quant':
            roomId = 'room-1'; // Technical Analysis
            break;
          case 'executive':
            roomId = 'room-2'; // Executive Suite
            break;
          case 'riskManager':
            roomId = 'room-3'; // Trading Floor
            break;
        }
        
        const position = getRandomPositionInRoom(roomId);
        const id = `${type}-${index}-${i}`;
        const name = getRandomName();
        
        // Create character
        const character: Character = {
          id,
          name,
          type,
          position,
          targetPosition: null,
          rotation: Math.random() * Math.PI * 2,
          currentRoom: roomId,
          state: 'idle',
          currentTask: null,
          conversations: [],
          skills: generateRandomSkills(type),
          activityHistory: [],
        };
        
        // Add character to store
        dispatch(addCharacter(character));
        
        // Log character creation
        dispatch(addLogEntry({
          id: Math.random().toString(36).substr(2, 9),
          timestamp: Date.now(),
          characterId: id,
          characterType: type,
          roomId,
          actionType: 'movement',
          description: `${name} (${type}) entered the simulation in ${roomId}`,
          details: { position }
        }));
      }
    });
    
    // Initialize performance metrics
    const initialPerformanceMetrics: PerformanceMetric[] = [
      { type: 'return', value: 0, timestamp: Date.now() },
      { type: 'alpha', value: 0, timestamp: Date.now() },
      { type: 'sharpe', value: 1.0, timestamp: Date.now() },
      { type: 'drawdown', value: 0, timestamp: Date.now() },
    ];
    
    initialPerformanceMetrics.forEach(metric => {
      dispatch(addPerformanceMetric(metric));
    });
  }, [dispatch]);
  
  // Function to update performance metrics
  const updatePerformanceMetrics = useCallback(() => {
    const timestamp = Date.now();
    
    // Generate random performance changes
    // In a real simulation, these would be calculated based on character decisions
    const returnChange = (Math.random() - 0.45) * 0.01; // Slight positive bias
    const alphaChange = (Math.random() - 0.48) * 0.005;
    const sharpeChange = (Math.random() - 0.5) * 0.1;
    const drawdownChange = Math.random() * 0.001;
    
    dispatch(addPerformanceMetric({ 
      type: 'return', 
      value: returnChange, 
      timestamp 
    }));
    
    dispatch(addPerformanceMetric({ 
      type: 'alpha', 
      value: alphaChange, 
      timestamp 
    }));
    
    dispatch(addPerformanceMetric({ 
      type: 'sharpe', 
      value: 1.0 + sharpeChange, 
      timestamp 
    }));
    
    dispatch(addPerformanceMetric({ 
      type: 'drawdown', 
      value: drawdownChange, 
      timestamp 
    }));
  }, [dispatch]);
  
  // Function to generate market events
  const generateMarketEvents = useCallback(() => {
    // Random chance to generate an event
    if (Math.random() < 0.1 && currentMarketEvents.length < 3) {
      const eventTemplate = MARKET_EVENT_TYPES[Math.floor(Math.random() * MARKET_EVENT_TYPES.length)];
      const possibleImpacts = eventTemplate.impacts;
      const impact = possibleImpacts[Math.floor(Math.random() * possibleImpacts.length)] as 'positive' | 'negative' | 'neutral';
      
      const magnitude = Math.random() * 0.1;
      
      // Generate descriptions based on event type and impact
      let description = '';
      switch (eventTemplate.type) {
        case 'Earnings Report':
          description = impact === 'positive' 
            ? 'Major company reports earnings above expectations' 
            : 'Key sector company misses earnings targets';
          break;
        case 'Fed Rate Decision':
          description = impact === 'positive'
            ? 'Federal Reserve cuts interest rates'
            : impact === 'negative'
              ? 'Federal Reserve raises interest rates unexpectedly'
              : 'Federal Reserve holds rates steady as expected';
          break;
        default:
          description = `${eventTemplate.type} with ${impact} market impact`;
      }
      
      const newEvent = {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: Date.now(),
        type: eventTemplate.type,
        description,
        impact,
        magnitude,
      };
      
      dispatch(addMarketEvent(newEvent));
      
      // Log the event
      dispatch(addLogEntry({
        id: Math.random().toString(36).substr(2, 9),
        timestamp: Date.now(),
        characterId: 'system',
        characterType: 'executive',
        roomId: 'system',
        actionType: 'analysis',
        description: `MARKET EVENT: ${description}`,
        details: { impact, magnitude }
      }));
      
      // Set timeout to remove the event
      setTimeout(() => {
        dispatch(removeMarketEvent(newEvent.id));
      }, 30000); // Events last for 30 seconds
    }
  }, [dispatch, currentMarketEvents]);
  
  // Function to make characters move between rooms
  const moveCharacters = useCallback(() => {
    characters.forEach(character => {
      // Only move idle characters, and not too frequently
      if (character.state === 'idle' && Math.random() < 0.02) {
        // Pick a random room
        const roomIds = Object.keys(ROOM_POSITIONS);
        let targetRoomId = roomIds[Math.floor(Math.random() * roomIds.length)];
        
        // Avoid moving to the same room
        if (targetRoomId === character.currentRoom && roomIds.length > 1) {
          // Pick a different room
          const otherRooms = roomIds.filter(id => id !== character.currentRoom);
          targetRoomId = otherRooms[Math.floor(Math.random() * otherRooms.length)];
        }
        
        // Get a random position in the target room
        const targetPosition = getRandomPositionInRoom(targetRoomId);
        
        // Set the character's target
        const target: Target = {
          position: targetPosition,
          roomId: targetRoomId,
        };
        
        dispatch(setCharacterTarget({ id: character.id, target }));
        dispatch(updateCharacterRoom({ id: character.id, roomId: targetRoomId }));
        
        // Log the movement
        dispatch(addLogEntry({
          id: Math.random().toString(36).substr(2, 9),
          timestamp: Date.now(),
          characterId: character.id,
          characterType: character.type,
          roomId: character.currentRoom,
          actionType: 'movement',
          description: `${character.name} is moving to ${targetRoomId}`,
          details: { from: character.currentRoom, to: targetRoomId }
        }));
        
        // Add to character history
        dispatch(addActivityToHistory({ 
          id: character.id, 
          activity: `Moving to ${targetRoomId}`
        }));
      }
    });
  }, [dispatch, characters]);
  
  // Function to make characters perform tasks
  const performCharacterTasks = useCallback(() => {
    characters.forEach(character => {
      // Only idle characters can start tasks
      if (character.state === 'idle' && Math.random() < 0.05) {
        // Set the character to working state
        dispatch(updateCharacterState({ 
          id: character.id, 
          state: 'working' 
        }));
        
        // Get task message based on character type
        const messages = CHARACTER_MESSAGES[character.type];
        const taskMessage = messages[Math.floor(Math.random() * messages.length)];
        
        dispatch(updateCharacterTask({ 
          id: character.id, 
          task: taskMessage 
        }));
        
        // Log the task
        dispatch(addLogEntry({
          id: Math.random().toString(36).substr(2, 9),
          timestamp: Date.now(),
          characterId: character.id,
          characterType: character.type,
          roomId: character.currentRoom,
          actionType: 'analysis',
          description: `${character.name} is ${taskMessage}`,
          details: { task: taskMessage }
        }));
        
        // Add to character history
        dispatch(addActivityToHistory({ 
          id: character.id, 
          activity: taskMessage 
        }));
        
        // Set timeout to finish the task
        setTimeout(() => {
          // Check if the character is still in the simulation
          const updatedCharacters = characters;
          const characterStillExists = updatedCharacters.some(c => c.id === character.id);
          
          if (characterStillExists) {
            dispatch(updateCharacterState({ 
              id: character.id, 
              state: 'idle' 
            }));
            
            dispatch(updateCharacterTask({ 
              id: character.id, 
              task: null 
            }));
            
            // Log task completion
            dispatch(addLogEntry({
              id: Math.random().toString(36).substr(2, 9),
              timestamp: Date.now(),
              characterId: character.id,
              characterType: character.type,
              roomId: character.currentRoom,
              actionType: 'decision',
              description: `${character.name} completed their task`,
              details: { task: taskMessage }
            }));
            
            // Add to character history
            dispatch(addActivityToHistory({ 
              id: character.id, 
              activity: `Completed: ${taskMessage}` 
            }));
          }
        }, Math.random() * 10000 + 5000); // Tasks take 5-15 seconds
      }
    });
  }, [dispatch, characters]);
  
  // Function to generate conversations between characters
  const generateConversations = useCallback(() => {
    // Group characters by room
    const charactersByRoom: Record<string, Character[]> = {};
    
    characters.forEach(character => {
      if (!charactersByRoom[character.currentRoom]) {
        charactersByRoom[character.currentRoom] = [];
      }
      charactersByRoom[character.currentRoom].push(character);
    });
    
    // For each room with multiple characters, possibly start a conversation
    Object.entries(charactersByRoom).forEach(([roomId, roomCharacters]) => {
      if (roomCharacters.length >= 2 && Math.random() < 0.03) {
        // Pick two random characters in the room
        const shuffled = [...roomCharacters].sort(() => 0.5 - Math.random());
        const char1 = shuffled[0];
        const char2 = shuffled[1];
        
        // Only start conversation if both are idle
        if (char1.state === 'idle' && char2.state === 'idle') {
          // Set both to talking state
          dispatch(updateCharacterState({ 
            id: char1.id, 
            state: 'talking' 
          }));
          
          dispatch(updateCharacterState({ 
            id: char2.id, 
            state: 'talking' 
          }));
          
          // Pick a random conversation topic
          const content = CONVERSATIONS[Math.floor(Math.random() * CONVERSATIONS.length)];
          const timestamp = Date.now();
          
          // Add conversation to both characters
          dispatch(addConversation({
            id: char1.id,
            withCharacterId: char2.id,
            content,
            timestamp
          }));
          
          dispatch(addConversation({
            id: char2.id,
            withCharacterId: char1.id,
            content: `Responding to: ${content}`,
            timestamp: timestamp + 1000
          }));
          
          // Log the conversation
          dispatch(addLogEntry({
            id: Math.random().toString(36).substr(2, 9),
            timestamp,
            characterId: char1.id,
            characterType: char1.type,
            roomId,
            actionType: 'communication',
            description: `${char1.name} is talking with ${char2.name}`,
            details: { message: content }
          }));
          
          // Add to character histories
          dispatch(addActivityToHistory({ 
            id: char1.id, 
            activity: `Discussing with ${char2.name}` 
          }));
          
          dispatch(addActivityToHistory({ 
            id: char2.id, 
            activity: `Discussing with ${char1.name}` 
          }));
          
          // Set timeout to end conversation
          setTimeout(() => {
            dispatch(updateCharacterState({ 
              id: char1.id, 
              state: 'idle' 
            }));
            
            dispatch(updateCharacterState({ 
              id: char2.id, 
              state: 'idle' 
            }));
            
            // Log conversation end
            dispatch(addLogEntry({
              id: Math.random().toString(36).substr(2, 9),
              timestamp: Date.now(),
              characterId: char1.id,
              characterType: char1.type,
              roomId,
              actionType: 'communication',
              description: `${char1.name} finished talking with ${char2.name}`,
              details: {}
            }));
          }, Math.random() * 5000 + 3000); // Conversations last 3-8 seconds
        }
      }
    });
  }, [dispatch, characters]);
  
  // Generate character events
  const generateCharacterEvents = useCallback(() => {
    // Only generate events during weekdays and active hours
    if (dayType === 'WEEKEND' || currentTimeOfDay === 'AFTER_HOURS') {
      return;
    }
    
    // Check if we should generate a new event
    const now = Date.now();
    const elapsedSinceLastEvent = now - lastEventGenerationTime;
    
    // Generate events less frequently when many active events
    const eventGenerationThreshold = Math.max(5000, 2000 + activeCharacterEvents.length * 2000);
    
    if (elapsedSinceLastEvent > eventGenerationThreshold && Math.random() < 0.3) {
      // Try to generate a random event
      const newEvent = generateRandomEvent(currentDate, characters, currentTimeOfDay);
      
      if (newEvent) {
        dispatch(addCharacterEvent(newEvent));
        setLastEventGenerationTime(now);
        
        // Log the event generation
        dispatch(addLogEntry({
          id: Math.random().toString(36).substr(2, 9),
          timestamp: now,
          characterId: newEvent.characterIds[0],
          characterType: characters.find(c => c.id === newEvent.characterIds[0])?.type || 'analyst',
          roomId: newEvent.originRoom,
          actionType: newEvent.eventType === 'ANALYZE' 
            ? 'analysis' 
            : newEvent.eventType === 'DISCUSS' 
              ? 'communication' 
              : newEvent.eventType === 'DECIDE' 
                ? 'decision' 
                : 'movement',
          description: `New event: ${newEvent.message}`,
          details: { eventType: newEvent.eventType, relatedStock: newEvent.relatedStock }
        }));
      }
    }
  }, [
    dispatch,
    lastEventGenerationTime,
    currentDate,
    characters,
    currentTimeOfDay,
    dayType,
    activeCharacterEvents.length
  ]);
  
  // Handle active character events
  const processCharacterEvents = useCallback(() => {
    // Check pending events that should be activated
    const currentTime = currentDate.getTime();
    
    // Check if there are pending events ready to be activated
    pendingCharacterEvents.forEach(event => {
      if (event.timestamp.getTime() <= currentTime) {
        // Activate the event
        dispatch(activateCharacterEvent(event.id));
        
        // Update character states for involved characters
        event.characterIds.forEach(charId => {
          const character = characters.find(c => c.id === charId);
          if (character) {
            // Set character to working or talking based on event type
            const newState = 
              event.eventType === 'DISCUSS' ? 'talking' : 
              event.eventType === 'MOVE' ? 'walking' : 'working';
            
            dispatch(updateCharacterState({ id: charId, state: newState }));
            
            if (event.eventType === 'DISCUSS' && event.characterIds.length > 1) {
              // For discussions, add conversation between characters
              const otherCharId = event.characterIds.find(id => id !== charId);
              if (otherCharId) {
                dispatch(addConversation({
                  id: charId,
                  withCharacterId: otherCharId,
                  content: event.message,
                  timestamp: Date.now()
                }));
              }
            } else {
              // For other events, set task
              dispatch(updateCharacterTask({ id: charId, task: event.message }));
            }
            
            // Add to activity history
            dispatch(addActivityToHistory({ 
              id: charId, 
              activity: event.message 
            }));
          }
        });
        
        // Set timeout to complete the event
        setTimeout(() => {
          dispatch(completeCharacterEvent(event.id));
          
          // Reset character states
          event.characterIds.forEach(charId => {
            dispatch(updateCharacterState({ id: charId, state: 'idle' }));
            dispatch(updateCharacterTask({ id: charId, task: null }));
          });
          
          // Log the event completion
          dispatch(addLogEntry({
            id: Math.random().toString(36).substr(2, 9),
            timestamp: Date.now(),
            characterId: event.characterIds[0],
            characterType: characters.find(c => c.id === event.characterIds[0])?.type || 'analyst',
            roomId: event.originRoom,
            actionType: event.eventType === 'ANALYZE' 
              ? 'analysis' 
              : event.eventType === 'DISCUSS' 
                ? 'communication' 
                : event.eventType === 'DECIDE' 
                  ? 'decision' 
                  : 'movement',
            description: `Completed: ${event.message}`,
            details: { eventType: event.eventType, relatedStock: event.relatedStock }
          }));
        }, event.duration);
      }
    });
  }, [
    dispatch, 
    currentDate, 
    pendingCharacterEvents, 
    characters
  ]);

  // Update simulation time and date
  const updateSimulation = useCallback(() => {
    const now = Date.now();
    const elapsed = now - lastUpdateTime;
    setLastUpdateTime(now);
    
    // Calculate real-time elapsed in milliseconds
    const simulationElapsed = elapsed * speed;
    const newSimulationTime = simulationTime + simulationElapsed;
    
    // Update simulation time
    dispatch(updateSimulationTime(newSimulationTime));
    
    // Update simulation date
    // 1 real-time second at 1x speed = 2 minutes in simulation time
    // This makes a workday (8 hours) take 4 minutes at 1x speed
    const simulationTimeMultiplier = 120; // 1 real second = 2 minutes (120 seconds)
    const simulationMillisecondsElapsed = simulationElapsed * simulationTimeMultiplier;
    
    // Calculate new date
    const newDate = new Date(currentDate.getTime() + simulationMillisecondsElapsed);
    
    // Check if we've moved to a new day
    if (lastDateRef.current && 
        newDate.getDate() !== lastDateRef.current.getDate()) {
      // Handle day transition - dispatch an event that we can listen for
      const dayCompleteEvent = new CustomEvent('dayComplete', { 
        detail: { 
          date: lastDateRef.current,
          nextDate: newDate
        } 
      });
      onDayComplete.dispatchEvent(dayCompleteEvent);
      
      // Only automatically pause if it's a weekday (for showing summary)
      if (lastDateRef.current.getDay() !== 0 && lastDateRef.current.getDay() !== 6) {
        dispatch(pauseSimulation());
      }
    }
    
    // Check if we've reached the end of the simulation
    if (newDate >= simulationEndDate) {
      dispatch(pauseSimulation());
      console.log("Simulation completed!");
      return;
    }
    
    dispatch(updateCurrentDate(newDate));
    lastDateRef.current = newDate;
    
    // Update day/night cycle (0-1 value representing progress through the day)
    // Map hours 0-24 to cycle value 0-1
    const hours = newDate.getHours();
    const minutes = newDate.getMinutes();
    const timeOfDayInMinutes = hours * 60 + minutes;
    const cycleProgress = timeOfDayInMinutes / (24 * 60);
    dispatch(updateDayNightCycle(cycleProgress));
    
    // Process any pending events
    processCharacterEvents();
    
    // Generate new character events occasionally
    generateCharacterEvents();
    
    // Only run these during business hours (9am-5pm) on weekdays
    const isBusinessHours = hours >= 9 && hours < 17;
    const isWeekday = newDate.getDay() !== 0 && newDate.getDay() !== 6;
    
    if (isBusinessHours && isWeekday) {
      // Update characters
      moveCharacters();
      performCharacterTasks();
      generateConversations();
      
      // Generate market events occasionally
      generateMarketEvents();
      
      // Update performance metrics occasionally
      if (Math.random() < 0.05) {
        updatePerformanceMetrics();
      }
    }
  }, [
    dispatch, 
    lastUpdateTime, 
    simulationTime, 
    currentDate,
    speed,
    simulationStartDate,
    simulationEndDate,
    moveCharacters, 
    performCharacterTasks, 
    generateConversations, 
    generateMarketEvents, 
    updatePerformanceMetrics,
    processCharacterEvents,
    generateCharacterEvents
  ]);
  
  // Main simulation loop
  useEffect(() => {
    if (characters.length === 0) {
      // Initialize the simulation if no characters exist
      initializeSimulation();
      setLastUpdateTime(Date.now());
    }
    
    let animationFrame: number;
    
    // Run the simulation loop when it's active
    if (isRunning) {
      const loop = () => {
        updateSimulation();
        animationFrame = requestAnimationFrame(loop);
      };
      
      animationFrame = requestAnimationFrame(loop);
    }
    
    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [isRunning, characters.length, initializeSimulation, updateSimulation]);
  
  return { simulationTime };
};

export default useSimulationEngine;
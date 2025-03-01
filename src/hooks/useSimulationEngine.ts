import { useEffect, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import { 
  updateSimulationTime, 
  updateDayNightCycle,
  addPerformanceMetric,
  addMarketEvent,
  removeMarketEvent,
  PerformanceMetric
} from '../store/simulationSlice';
import { 
  addCharacter, 
  setCharacterTarget, 
  updateCharacterState,
  updateCharacterTask,
  addConversation,
  addActivityToHistory,
  Character,
  updateCharacterRoom
} from '../store/charactersSlice';
import { addLogEntry } from '../store/activityLogSlice';
import { Position, Target } from '../store/charactersSlice';
import { CharacterType } from '../models/types';

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

// Hook for simulation engine
const useSimulationEngine = () => {
  const dispatch = useDispatch();
  const { isRunning, speed, simulationTime, currentMarketEvents } = useSelector(
    (state: RootState) => state.simulation
  );
  const characters = useSelector((state: RootState) => state.characters.characters);
  
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  
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
  
  // Update simulation time
  const updateSimulation = useCallback(() => {
    const now = Date.now();
    const elapsed = now - lastUpdateTime;
    setLastUpdateTime(now);
    
    // Update simulation time
    dispatch(updateSimulationTime(simulationTime + elapsed * speed));
    
    // Update day/night cycle (full cycle every 5 minutes of real time)
    const cycleProgress = (simulationTime % (5 * 60 * 1000)) / (5 * 60 * 1000);
    dispatch(updateDayNightCycle(cycleProgress));
    
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
  }, [
    dispatch, 
    lastUpdateTime, 
    simulationTime, 
    speed, 
    moveCharacters, 
    performCharacterTasks, 
    generateConversations, 
    generateMarketEvents, 
    updatePerformanceMetrics
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
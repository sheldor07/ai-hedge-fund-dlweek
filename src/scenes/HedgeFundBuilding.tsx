import React, { useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setFocusedEntity } from '../store/simulationSlice';
import { RoomType } from '../models/types';
import * as THREE from 'three';
import { Box, Text } from '@react-three/drei';
import FurnitureItem from '../components/FurnitureItem';
import { ROOM_COLORS, FLOOR_COLOR, CORRIDOR_COLOR, GRASS_COLOR, FURNITURE_MODELS } from '../utils/modelLoader';

// Define the room layout for the hedge fund building
const ROOMS = [
  {
    id: 'room-0',
    type: 'fundamentalAnalysis' as RoomType,
    name: 'Fundamental Analysis',
    position: { x: -8, y: 0, z: -8 },  // Updated Y position
    size: { width: 7, height: 3, depth: 7 },
  },
  {
    id: 'room-1',
    type: 'technicalAnalysis' as RoomType,
    name: 'Technical Analysis',
    position: { x: 8, y: 0, z: -8 },
    size: { width: 7, height: 3, depth: 7 },
  },
  {
    id: 'room-2',
    type: 'executiveSuite' as RoomType,
    name: 'Executive Suite',
    position: { x: -8, y: 0, z: 8 },
    size: { width: 7, height: 3, depth: 7 },
  },
  {
    id: 'room-3',
    type: 'tradingFloor' as RoomType,
    name: 'Trading Floor',
    position: { x: 8, y: 0, z: 8 },
    size: { width: 7, height: 3, depth: 7 },
  },
];

// Room component for each individual room
const Room: React.FC<{
  room: typeof ROOMS[0];
  isSelected: boolean;
  onClick: () => void;
}> = ({ room, isSelected, onClick }) => {
  // Get furniture models for this room type
  const furnitureItems = FURNITURE_MODELS[room.type] || [];

  return (
    <group position={[room.position.x, room.position.y, room.position.z]} onClick={onClick}>
      {/* Room floor */}
      <Box
        args={[room.size.width, 0.1, room.size.depth]}
        position={[0, -0.5, 0]} // Lower the floor significantly, placing it on the ground level
        receiveShadow
      >
        <meshStandardMaterial 
          color={FLOOR_COLOR} 
          metalness={0.1}
          roughness={0.9}
          // Add a subtle pattern with normal map would be ideal here
        />
      </Box>
      
      {/* Room walls - using the Crossy Road style with block-like walls */}
      {/* Create four walls with a door cutout in the front */}
      <group>
        {/* Left part of front wall */}
        <Box
          args={[room.size.width/2 - 0.75, room.size.height, 0.2]}
          position={[-room.size.width/4 - 0.75/2, room.size.height/2 - 0.5, -room.size.depth/2]}
          castShadow
          receiveShadow
        >
          <meshStandardMaterial 
            color={ROOM_COLORS[room.type]} 
            opacity={0.6} 
            transparent
            emissive={ROOM_COLORS[room.type]}
            emissiveIntensity={isSelected ? 0.5 : 0.2}
            metalness={0.2}
            roughness={0.7}
          />
        </Box>
        
        {/* Right part of front wall */}
        <Box
          args={[room.size.width/2 - 0.75, room.size.height, 0.2]}
          position={[room.size.width/4 + 0.75/2, room.size.height/2 - 0.5, -room.size.depth/2]}
          castShadow
          receiveShadow
        >
          <meshStandardMaterial 
            color={ROOM_COLORS[room.type]} 
            opacity={0.6} 
            transparent
            emissive={ROOM_COLORS[room.type]}
            emissiveIntensity={isSelected ? 0.5 : 0.2}
            metalness={0.2}
            roughness={0.7}
          />
        </Box>
        
        {/* Top part of front wall (above door) */}
        <Box
          args={[1.5, room.size.height - 2, 0.2]}
          position={[0, room.size.height - 1 - 0.5, -room.size.depth/2]}
          castShadow
          receiveShadow
        >
          <meshStandardMaterial 
            color={ROOM_COLORS[room.type]} 
            opacity={0.6} 
            transparent
            emissive={ROOM_COLORS[room.type]}
            emissiveIntensity={isSelected ? 0.5 : 0.2}
            metalness={0.2}
            roughness={0.7}
          />
        </Box>
      </group>
      
      {/* Back wall */}
      <Box
        args={[room.size.width, room.size.height, 0.2]}
        position={[0, room.size.height/2 - 0.5, room.size.depth/2]}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial 
          color={ROOM_COLORS[room.type]} 
          opacity={0.6} 
          transparent
          emissive={ROOM_COLORS[room.type]}
          emissiveIntensity={isSelected ? 0.5 : 0.2}
          metalness={0.2}
          roughness={0.7}
        />
      </Box>
      
      {/* Left wall */}
      <Box
        args={[0.2, room.size.height, room.size.depth]}
        position={[-room.size.width/2, room.size.height/2 - 0.5, 0]}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial 
          color={ROOM_COLORS[room.type]} 
          opacity={0.6} 
          transparent
          emissive={ROOM_COLORS[room.type]}
          emissiveIntensity={isSelected ? 0.5 : 0.2}
          metalness={0.2}
          roughness={0.7}
        />
      </Box>
      
      {/* Right wall */}
      <Box
        args={[0.2, room.size.height, room.size.depth]}
        position={[room.size.width/2, room.size.height/2 - 0.5, 0]}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial 
          color={ROOM_COLORS[room.type]} 
          opacity={0.6} 
          transparent
          emissive={ROOM_COLORS[room.type]}
          emissiveIntensity={isSelected ? 0.5 : 0.2}
          metalness={0.2}
          roughness={0.7}
        />
      </Box>
      
      {/* Roof */}
      <Box
        args={[room.size.width, 0.2, room.size.depth]}
        position={[0, room.size.height - 0.5, 0]}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial 
          color={ROOM_COLORS[room.type]} 
          opacity={0.6} 
          transparent
          emissive={ROOM_COLORS[room.type]}
          emissiveIntensity={isSelected ? 0.5 : 0.2}
          metalness={0.2}
          roughness={0.7}
        />
      </Box>
      
      {/* Room Furniture based on room type */}
      {furnitureItems.map((item, index) => (
        item.positions.map((position, posIndex) => (
          <FurnitureItem
            key={`${item.name}-${index}-${posIndex}`}
            modelPath={item.model}
            position={position as [number, number, number]}
            scale={item.scale || 1}
            rotation={item.rotation as [number, number, number] || [0, 0, 0]}
          />
        ))
      ))}
      
      {/* Room name label */}
      <Text
        position={[0, room.size.height - 0.5 + 0.5, 0]}
        color="black"
        fontSize={0.4}
        maxWidth={room.size.width - 1}
        textAlign="center"
        anchorX="center"
        anchorY="middle"
      >
        {room.name}
      </Text>
    </group>
  );
};

// Main HedgeFundBuilding component
const HedgeFundBuilding: React.FC = () => {
  const dispatch = useDispatch();
  const focusedEntity = useSelector((state: RootState) => state.simulation.focusedEntity);
  
  // Animation for central displays (market data screens)
  const time = useRef(0);
  
  // Using useFrame from react-three-fiber would be better here, but keeping the ref approach
  // to minimize code changes while fixing performance
  
  const handleRoomClick = (roomId: string) => {
    dispatch(setFocusedEntity({ type: 'room', id: roomId }));
  };

  // Get central area furniture models
  const centralFurniture = FURNITURE_MODELS.centralArea || [];

  return (
    <group>
      {/* Base ground plane (grass) */}
      <mesh 
        position={[0, -0.5, 0]} 
        rotation={[-Math.PI / 2, 0, 0]} 
        receiveShadow
      >
        <planeGeometry args={[50, 50]} />
        <meshStandardMaterial 
          color={GRASS_COLOR} 
          metalness={0.0}
          roughness={1.0}
        />
      </mesh>
      
      {/* Building foundation */}
      <mesh
        position={[0, -0.25, 0]}
        receiveShadow
      >
        <boxGeometry args={[30, 0.5, 30]} />
        <meshStandardMaterial 
          color="#9e9e9e" 
          metalness={0.2}
          roughness={0.8}
        />
      </mesh>

      {/* Main corridors */}
      <Box
        args={[20, 0.1, 2]}
        position={[0, -0.45, 0]}
        receiveShadow
      >
        <meshStandardMaterial 
          color={CORRIDOR_COLOR} 
          metalness={0.1}
          roughness={0.7}
        />
      </Box>
      <Box
        args={[2, 0.1, 20]}
        position={[0, -0.45, 0]}
        receiveShadow
      >
        <meshStandardMaterial 
          color={CORRIDOR_COLOR} 
          metalness={0.1}
          roughness={0.7}
        />
      </Box>
      
      {/* Central area furniture for immersion */}
      {centralFurniture.map((item, index) => (
        item.positions.map((position, posIndex) => (
          <FurnitureItem
            key={`central-${item.name}-${index}-${posIndex}`}
            modelPath={item.model}
            position={position as [number, number, number]}
            scale={item.scale || 1}
            rotation={item.rotation as [number, number, number] || [0, 0, 0]}
          />
        ))
      ))}
      
      {/* Animated market data hologram in the center */}
      <group position={[0, 1.5, 0]}>
        <mesh>
          <sphereGeometry args={[0.5, 16, 16]} />
          <meshStandardMaterial 
            color="#2196f3" 
            emissive="#2196f3" 
            emissiveIntensity={1.2} 
            transparent 
            opacity={0.7}
            metalness={0.8}
            roughness={0.2}
          />
        </mesh>
        
        {/* Market data lines - static positions to reduce animation overhead */}
        {[...Array(8)].map((_, i) => {
          // Pre-calculated static positions based on the index
          const angle = i * Math.PI / 4;
          return (
            <mesh 
              key={`market-line-${i}`} 
              position={[
                Math.sin(angle) * 0.7, 
                Math.cos(angle) * 0.3, 
                Math.cos(angle) * 0.7
              ]}
            >
              <boxGeometry args={[0.8, 0.05, 0.05]} />
              <meshStandardMaterial 
                color={i % 2 === 0 ? "#4caf50" : "#f44336"} 
                emissive={i % 2 === 0 ? "#4caf50" : "#f44336"} 
                emissiveIntensity={1.2} 
                transparent 
                opacity={0.9}
                metalness={0.8}
                roughness={0.2}
              />
            </mesh>
          );
        })}
      </group>

      {/* Render all rooms */}
      {ROOMS.map((room) => (
        <Room
          key={room.id}
          room={room}
          isSelected={focusedEntity.type === 'room' && focusedEntity.id === room.id}
          onClick={() => handleRoomClick(room.id)}
        />
      ))}
      
      {/* Enhanced lighting for better immersion and atmosphere */}
      <ambientLight intensity={0.4} /> {/* Reduced ambient to create more contrast */}
      
      {/* Main light source with shadows */}
      <pointLight 
        position={[0, 5, 0]} 
        intensity={800} 
        color="#ffffff"
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-bias={-0.001}
      />
      
      {/* Blue accent light */}
      <pointLight 
        position={[0, 1, 0]} 
        intensity={300} 
        color="#2196f3"
        distance={15}
        decay={2}
      />
      
      {/* Additional colored accent lights for each corner */}
      <pointLight 
        position={[-10, 1, -10]} 
        intensity={150} 
        color="#1976d2" /* Blue for fundamental analysis corner */
        distance={8}
        decay={2}
      />
      <pointLight 
        position={[10, 1, -10]} 
        intensity={150} 
        color="#2e7d32" /* Green for technical analysis corner */
        distance={8}
        decay={2}
      />
      <pointLight 
        position={[-10, 1, 10]} 
        intensity={150} 
        color="#e65100" /* Orange for executive suite corner */
        distance={8}
        decay={2}
      />
      <pointLight 
        position={[10, 1, 10]} 
        intensity={150} 
        color="#d32f2f" /* Red for trading floor corner */
        distance={8}
        decay={2}
      />
    </group>
  );
};

export default HedgeFundBuilding;
import React, { useRef, useEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Html, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import { 
  updateCharacterPosition, 
  updateCharacterState,
  updateCharacterRotation,
  Character as CharacterType
} from '../store/charactersSlice';
import { setFocusedEntity } from '../store/simulationSlice';
import { addLogEntry } from '../store/activityLogSlice';
import { CHARACTER_COLORS } from '../utils/modelLoader';

interface CharacterProps {
  character: CharacterType;
}

const CHARACTER_SPEED = 0.05;

// Blocky character model component based on Kenney's assets
const BlockyCharacter: React.FC<{ 
  type: string,
  color: string,
  scale?: number,
  focused: boolean
}> = ({ type, color, scale = 1.3, focused }) => { // Increased default scale for better visibility
  // Body parts with Crossy Road style
  return (
    <group scale={[scale, scale, scale]}>
      {/* Character outline for better visibility */}
      <mesh castShadow position={[0, 0.5, 0]}>
        <boxGeometry args={[0.68, 0.88, 0.48]} />
        <meshStandardMaterial 
          color={'#000000'} 
          transparent
          opacity={0.8}
        />
      </mesh>
      
      {/* Body */}
      <mesh castShadow position={[0, 0.5, 0]}>
        <boxGeometry args={[0.6, 0.8, 0.4]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color}
          emissiveIntensity={focused ? 0.5 : 0.2}
          metalness={0.3}
          roughness={0.7}
        />
      </mesh>
      
      {/* Head */}
      <mesh castShadow position={[0, 1.15, 0]}>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial 
          color={focused ? color : '#f5d7b5'} 
          emissive={focused ? color : '#000000'}
          emissiveIntensity={focused ? 0.5 : 0}
          metalness={0.1}
          roughness={0.8}
        />
      </mesh>
      
      {/* Eyes */}
      <mesh position={[0.12, 1.15, 0.26]}>
        <boxGeometry args={[0.1, 0.1, 0.05]} />
        <meshStandardMaterial color="black" />
      </mesh>
      <mesh position={[-0.12, 1.15, 0.26]}>
        <boxGeometry args={[0.1, 0.1, 0.05]} />
        <meshStandardMaterial color="black" />
      </mesh>
      
      {/* Mouth */}
      <mesh position={[0, 1.0, 0.26]}>
        <boxGeometry args={[0.2, 0.05, 0.05]} />
        <meshStandardMaterial color="black" />
      </mesh>
      
      {/* Arms */}
      <mesh castShadow position={[0.4, 0.5, 0]}>
        <boxGeometry args={[0.2, 0.6, 0.2]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh castShadow position={[-0.4, 0.5, 0]}>
        <boxGeometry args={[0.2, 0.6, 0.2]} />
        <meshStandardMaterial color={color} />
      </mesh>
      
      {/* Legs */}
      <mesh castShadow position={[0.2, 0, 0]}>
        <boxGeometry args={[0.2, 0.6, 0.2]} />
        <meshStandardMaterial color="#1976d2" />
      </mesh>
      <mesh castShadow position={[-0.2, 0, 0]}>
        <boxGeometry args={[0.2, 0.6, 0.2]} />
        <meshStandardMaterial color="#1976d2" />
      </mesh>
      
      {/* Character-specific accessories */}
      {type === 'analyst' && (
        <>
          {/* Glasses */}
          <mesh position={[0, 1.15, 0.28]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.4, 0.1, 0.05]} />
            <meshStandardMaterial color="#424242" />
          </mesh>
          {/* Laptop/tablet */}
          <mesh position={[0.35, 0.4, 0.25]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.3, 0.2, 0.05]} />
            <meshStandardMaterial color="#78909c" />
          </mesh>
        </>
      )}
      
      {type === 'quant' && (
        <>
          {/* Calculator */}
          <mesh position={[0.35, 0.4, 0.2]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.15, 0.2, 0.05]} />
            <meshStandardMaterial color="#212121" />
          </mesh>
          {/* Tie */}
          <mesh position={[0, 0.7, 0.22]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.1, 0.3, 0.02]} />
            <meshStandardMaterial color="#d32f2f" />
          </mesh>
        </>
      )}
      
      {type === 'executive' && (
        <>
          {/* Suit style body with tie */}
          <mesh position={[0, 0.7, 0.22]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.1, 0.3, 0.02]} />
            <meshStandardMaterial color="#212121" />
          </mesh>
          {/* Phone */}
          <mesh position={[0.35, 0.6, 0.15]} rotation={[0, 0, Math.PI/4]}>
            <boxGeometry args={[0.1, 0.2, 0.02]} />
            <meshStandardMaterial color="#424242" />
          </mesh>
          {/* Executive hair/hairstyle */}
          <mesh position={[0, 1.4, 0]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.5, 0.1, 0.4]} />
            <meshStandardMaterial color="#5d4037" />
          </mesh>
        </>
      )}
      
      {type === 'riskManager' && (
        <>
          {/* Clipboard */}
          <mesh position={[0.35, 0.4, 0.2]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.25, 0.3, 0.03]} />
            <meshStandardMaterial color="#e0e0e0" />
          </mesh>
          {/* ID Badge */}
          <mesh position={[0, 0.6, 0.22]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.15, 0.15, 0.02]} />
            <meshStandardMaterial color="#fff176" />
          </mesh>
          {/* Glasses for risk manager */}
          <mesh position={[0, 1.15, 0.28]} rotation={[0, 0, 0]}>
            <boxGeometry args={[0.4, 0.1, 0.05]} />
            <meshStandardMaterial color="#616161" />
          </mesh>
        </>
      )}
    </group>
  );
};

// Main Character component
const Character: React.FC<CharacterProps> = ({ character }) => {
  const dispatch = useDispatch();
  const characterRef = useRef<THREE.Group>(null);
  const targetRef = useRef<THREE.Vector3 | null>(null);
  const simulationSpeed = useSelector((state: RootState) => state.simulation.speed);
  const focused = useSelector((state: RootState) => 
    state.simulation.focusedEntity.type === 'character' && 
    state.simulation.focusedEntity.id === character.id
  );
  const [showSpeechBubble, setShowSpeechBubble] = useState(false);
  const [speechBubbleContent, setSpeechBubbleContent] = useState('');

  // Effect to handle speech bubbles
  useEffect(() => {
    if (character.state === 'talking' && character.conversations.length > 0) {
      const latestConversation = character.conversations[character.conversations.length - 1];
      setSpeechBubbleContent(latestConversation.content);
      setShowSpeechBubble(true);
      
      // Hide speech bubble after a few seconds
      const timer = setTimeout(() => {
        setShowSpeechBubble(false);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [character.state, character.conversations]);

  // Update target when character's target position changes
  useEffect(() => {
    if (character.targetPosition) {
      targetRef.current = new THREE.Vector3(
        character.targetPosition.position.x,
        character.targetPosition.position.y,
        character.targetPosition.position.z
      );
      
      if (character.state !== 'walking') {
        dispatch(updateCharacterState({ id: character.id, state: 'walking' }));
        
        // Log movement activity
        dispatch(addLogEntry({
          id: Math.random().toString(36).substr(2, 9),
          timestamp: Date.now(),
          characterId: character.id,
          characterType: character.type,
          roomId: character.currentRoom,
          actionType: 'movement',
          description: `${character.name} started moving`,
          details: { 
            from: character.position, 
            to: character.targetPosition.position 
          }
        }));
      }
    } else {
      targetRef.current = null;
      
      if (character.state === 'walking') {
        dispatch(updateCharacterState({ id: character.id, state: 'idle' }));
      }
    }
  }, [character.targetPosition, dispatch, character.id, character.state, character.name, character.type, character.currentRoom, character.position]);

  // Handle movement and animation in the frame loop
  useFrame(() => {
    if (characterRef.current && targetRef.current) {
      const position = characterRef.current.position;
      const target = targetRef.current;
      
      // Calculate distance to target
      const distance = position.distanceTo(target);
      
      if (distance > 0.1) {
        // Calculate direction vector
        const direction = new THREE.Vector3().subVectors(target, position).normalize();
        
        // Move towards target
        position.add(direction.multiplyScalar(CHARACTER_SPEED * simulationSpeed));
        
        // Calculate rotation to face movement direction
        const angle = Math.atan2(direction.x, direction.z);
        dispatch(updateCharacterRotation({ 
          id: character.id, 
          rotation: angle 
        }));
        
        // Update character position in Redux store
        dispatch(updateCharacterPosition({
          id: character.id,
          position: {
            x: position.x,
            y: position.y,
            z: position.z
          }
        }));
      } else {
        // Reached target
        targetRef.current = null;
        
        if (character.state === 'walking') {
          dispatch(updateCharacterState({ id: character.id, state: 'idle' }));
          
          // Log arrival
          dispatch(addLogEntry({
            id: Math.random().toString(36).substr(2, 9),
            timestamp: Date.now(),
            characterId: character.id,
            characterType: character.type,
            roomId: character.currentRoom,
            actionType: 'movement',
            description: `${character.name} arrived at destination`,
            details: { position: character.position }
          }));
        }
      }
    }
  });

  const handleCharacterClick = () => {
    dispatch(setFocusedEntity({ type: 'character', id: character.id }));
  };
  
  // Add walking/bobbing animation based on character state
  const [bobOffset, setBobOffset] = useState(0);
  
  useFrame(({ clock }) => {
    if (character.state === 'walking') {
      // Simple bobbing animation when walking
      setBobOffset(Math.sin(clock.getElapsedTime() * 10) * 0.05);
    } else {
      // Subtle idle animation
      setBobOffset(Math.sin(clock.getElapsedTime() * 2) * 0.02);
    }
  });

  return (
    <group 
      ref={characterRef} 
      position={[character.position.x, character.position.y + bobOffset, character.position.z]}
      rotation={[0, character.rotation, 0]}
      onClick={handleCharacterClick}
    >
      {/* Use the Blocky Character model */}
      <BlockyCharacter 
        type={character.type} 
        color={CHARACTER_COLORS[character.type]}
        focused={focused}
        scale={1}
      />
      
      {/* Name tag */}
      <Text
        position={[0, 2, 0]}
        color="black"
        fontSize={0.3}
        anchorX="center"
        anchorY="middle"
      >
        {character.name}
      </Text>
      
      {/* Speech bubble */}
      {showSpeechBubble && (
        <Html
          position={[0, 2.5, 0]}
          center
          style={{
            backgroundColor: 'white',
            padding: '5px 10px',
            borderRadius: '10px',
            boxShadow: '0 0 5px rgba(0,0,0,0.2)',
            width: '150px',
            textAlign: 'center',
            fontSize: '14px',
            transform: 'translate(-50%, -50%)',
          }}
        >
          {speechBubbleContent}
        </Html>
      )}
      
      {/* State indicator */}
      <Html
        position={[0, -0.5, 0]}
        center
        style={{
          backgroundColor: focused ? '#ffff00' : '#ffffff',
          color: '#000000',
          padding: '2px 5px',
          borderRadius: '4px',
          fontSize: '10px',
          opacity: 0.8,
          pointerEvents: 'none',
          width: '60px',
          textAlign: 'center',
        }}
      >
        {character.state}
      </Html>
    </group>
  );
};

export default Character;
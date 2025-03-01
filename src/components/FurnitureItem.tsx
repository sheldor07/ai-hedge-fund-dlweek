import React, { useRef, useState, useEffect } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

// This component handles furniture models from Kenney's furniture kit
interface FurnitureProps {
  modelPath: string;
  position: [number, number, number];
  scale?: number;
  rotation?: [number, number, number];
  color?: string;
}

// Function to check if a model path includes any of the provided keywords
const includesAny = (str: string, keywords: string[]): boolean => {
  return keywords.some(keyword => str.includes(keyword));
};

// Enhanced furniture component with better visuals and animations
const FurnitureItem: React.FC<FurnitureProps> = ({
  modelPath,
  position,
  scale = 1,
  rotation = [0, 0, 0],
  color
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);
  const [time, setTime] = useState(0);
  
  // Increment time for animations - using a ref instead of state to avoid re-renders
  const timeRef = useRef(0);
  
  useEffect(() => {
    let animationFrame: number;
    const animate = () => {
      timeRef.current += 0.01;
      animationFrame = requestAnimationFrame(animate);
    };
    
    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, []);
  
  // Furniture type checks
  const isDesk = includesAny(modelPath, ['desk', 'table']);
  const isChair = modelPath.includes('chair');
  const isComputer = includesAny(modelPath, ['computer', 'television', 'monitor', 'screen', 'laptop']);
  const isStorage = includesAny(modelPath, ['bookcase', 'cabinet', 'shelf']);
  const isPlant = modelPath.includes('plant');
  const isRug = modelPath.includes('rug');
  const isLamp = includesAny(modelPath, ['lamp', 'light']);
  
  // Define more vibrant colors for different furniture types
  const deskColor = color || '#8d6e63';      // Brown
  const chairColor = color || '#a1887f';     // Light brown
  const computerColor = color || '#424242';  // Dark gray
  const storageColor = color || '#6d4c41';   // Dark brown
  const plantColor = color || '#66bb6a';     // Green
  const rugColor = color || '#80cbc4';       // Teal
  const lampColor = color || '#ffb74d';      // Orange
  
  // Animation variables
  const hoverScale = hovered ? 1.05 : 1;
  const computerColorPulse = isComputer ? 
    new THREE.Color().setHSL(0.6 + Math.sin(timeRef.current * 2) * 0.1, 0.8, 0.5) : 
    new THREE.Color('#1e88e5');
  
  // Apply a Y offset to position furniture correctly on the floor
  const positionWithFloorOffset: [number, number, number] = [
    position[0],
    position[1] - 0.2, // Subtract 0.2 to position relative to lowered floor
    position[2]
  ];

  return (
    <group 
      ref={groupRef} 
      position={positionWithFloorOffset} 
      rotation={rotation as any} 
      scale={[scale * hoverScale, scale * hoverScale, scale * hoverScale]}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      {isDesk && (
        <mesh castShadow receiveShadow>
          <boxGeometry args={[1, 0.05, 0.5]} />
          <meshStandardMaterial color={deskColor} roughness={0.7} metalness={0.2} />
          
          {/* Table legs */}
          <mesh position={[0.4, -0.25, 0.2]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={deskColor} roughness={0.7} />
          </mesh>
          <mesh position={[-0.4, -0.25, 0.2]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={deskColor} roughness={0.7} />
          </mesh>
          <mesh position={[0.4, -0.25, -0.2]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={deskColor} roughness={0.7} />
          </mesh>
          <mesh position={[-0.4, -0.25, -0.2]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={deskColor} roughness={0.7} />
          </mesh>
        </mesh>
      )}
      
      {isChair && (
        <group>
          {/* Seat */}
          <mesh position={[0, 0, 0]} castShadow>
            <boxGeometry args={[0.4, 0.05, 0.4]} />
            <meshStandardMaterial color={chairColor} roughness={0.5} />
          </mesh>
          
          {/* Back */}
          <mesh position={[0, 0.25, -0.2]} castShadow>
            <boxGeometry args={[0.4, 0.5, 0.05]} />
            <meshStandardMaterial color={chairColor} roughness={0.5} />
          </mesh>
          
          {/* Legs */}
          <mesh position={[0.15, -0.25, 0.15]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={chairColor} roughness={0.3} metalness={0.5} />
          </mesh>
          <mesh position={[-0.15, -0.25, 0.15]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={chairColor} roughness={0.3} metalness={0.5} />
          </mesh>
          <mesh position={[0.15, -0.25, -0.15]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={chairColor} roughness={0.3} metalness={0.5} />
          </mesh>
          <mesh position={[-0.15, -0.25, -0.15]} castShadow>
            <boxGeometry args={[0.05, 0.5, 0.05]} />
            <meshStandardMaterial color={chairColor} roughness={0.3} metalness={0.5} />
          </mesh>
        </group>
      )}
      
      {isComputer && (
        <group>
          {/* Screen */}
          <mesh position={[0, 0, 0]} castShadow>
            <boxGeometry args={[0.4, 0.3, 0.05]} />
            <meshStandardMaterial color={computerColor} roughness={0.2} metalness={0.8} />
          </mesh>
          
          {/* Screen content (animated and glowing) */}
          <mesh position={[0, 0, 0.03]} castShadow>
            <boxGeometry args={[0.35, 0.25, 0.01]} />
            <meshStandardMaterial 
              color={computerColorPulse} 
              emissive={computerColorPulse} 
              emissiveIntensity={0.8} 
              transparent
              opacity={0.9}
            />
          </mesh>
          
          {/* Data lines on screen (animated) */}
          {[...Array(4)].map((_, i) => (
            <mesh 
              key={`data-line-${i}`} 
              position={[0, 0.05 - i * 0.05, 0.035]} 
              castShadow
            >
              <boxGeometry args={[0.3 * (0.7 + Math.sin(timeRef.current * 3 + i) * 0.3), 0.02, 0.005]} />
              <meshStandardMaterial 
                color={i % 2 === 0 ? "#4caf50" : "#f44336"} 
                emissive={i % 2 === 0 ? "#4caf50" : "#f44336"} 
                emissiveIntensity={0.8}
              />
            </mesh>
          ))}
          
          {/* Base */}
          <mesh position={[0, -0.2, 0.05]} castShadow>
            <boxGeometry args={[0.15, 0.1, 0.1]} />
            <meshStandardMaterial color={computerColor} roughness={0.4} metalness={0.6} />
          </mesh>
        </group>
      )}
      
      {isStorage && (
        <group>
          {/* Main cabinet */}
          <mesh position={[0, 0, 0]} castShadow>
            <boxGeometry args={[0.8, 1, 0.4]} />
            <meshStandardMaterial color={storageColor} roughness={0.6} />
          </mesh>
          
          {/* Shelves */}
          <mesh position={[0, 0.2, 0]} castShadow>
            <boxGeometry args={[0.78, 0.02, 0.38]} />
            <meshStandardMaterial color={storageColor} roughness={0.7} />
          </mesh>
          <mesh position={[0, -0.2, 0]} castShadow>
            <boxGeometry args={[0.78, 0.02, 0.38]} />
            <meshStandardMaterial color={storageColor} roughness={0.7} />
          </mesh>
          
          {/* Doors/divisions */}
          <mesh position={[0, 0, 0.19]} castShadow>
            <boxGeometry args={[0.78, 0.98, 0.02]} />
            <meshStandardMaterial color={storageColor} roughness={0.5} />
          </mesh>
          
          {/* Door handles */}
          <mesh position={[-0.2, 0, 0.2]} rotation={[Math.PI/2, 0, 0]} castShadow>
            <cylinderGeometry args={[0.02, 0.02, 0.06, 8]} />
            <meshStandardMaterial color={"#b0bec5"} metalness={0.8} roughness={0.2} />
          </mesh>
          <mesh position={[0.2, 0, 0.2]} rotation={[Math.PI/2, 0, 0]} castShadow>
            <cylinderGeometry args={[0.02, 0.02, 0.06, 8]} />
            <meshStandardMaterial color={"#b0bec5"} metalness={0.8} roughness={0.2} />
          </mesh>
        </group>
      )}
      
      {isPlant && (
        <group>
          {/* Pot */}
          <mesh position={[0, -0.15, 0]} castShadow>
            <cylinderGeometry args={[0.15, 0.1, 0.3, 12]} />
            <meshStandardMaterial color="#5d4037" roughness={0.8} />
          </mesh>
          
          {/* Plant base */}
          <mesh position={[0, 0.1, 0]} castShadow>
            <sphereGeometry args={[0.25, 16, 16]} />
            <meshStandardMaterial color={plantColor} roughness={0.9} />
          </mesh>
          
          {/* Plant leaves - dynamic movement */}
          {[...Array(5)].map((_, i) => (
            <mesh 
              key={`leaf-${i}`} 
              position={[
                Math.sin(i * Math.PI * 0.4) * 0.15, 
                0.2 + Math.sin(timeRef.current + i) * 0.02, 
                Math.cos(i * Math.PI * 0.4) * 0.15
              ]} 
              castShadow
            >
              <sphereGeometry args={[0.1, 8, 8]} />
              <meshStandardMaterial 
                color={new THREE.Color().setHSL(0.3, 0.7, 0.4 + i * 0.05)} 
                roughness={0.8} 
              />
            </mesh>
          ))}
        </group>
      )}
      
      {isRug && (
        <mesh position={[0, 0, 0]} receiveShadow rotation={[0, 0, 0]}>
          <boxGeometry args={[1, 0.02, 0.6]} />
          <meshStandardMaterial 
            color={rugColor} 
            roughness={0.9} 
            transparent 
            opacity={0.9} 
          />
        </mesh>
      )}
      
      {isLamp && (
        <group>
          {/* Lamp base */}
          <mesh position={[0, -0.2, 0]} castShadow>
            <cylinderGeometry args={[0.1, 0.15, 0.1, 16]} />
            <meshStandardMaterial color={lampColor} metalness={0.3} roughness={0.5} />
          </mesh>
          
          {/* Lamp stand */}
          <mesh position={[0, 0, 0]} castShadow>
            <cylinderGeometry args={[0.02, 0.02, 0.5, 8]} />
            <meshStandardMaterial color={"#b0bec5"} metalness={0.6} roughness={0.3} />
          </mesh>
          
          {/* Lamp shade */}
          <mesh position={[0, 0.2, 0]} rotation={[Math.PI, 0, 0]} castShadow>
            <coneGeometry args={[0.2, 0.3, 16, 1, true]} />
            <meshStandardMaterial 
              color={"#ffecb3"} 
              transparent 
              opacity={0.8} 
              side={THREE.DoubleSide}
              emissive={"#ffecb3"}
              emissiveIntensity={hovered ? 0.5 : 0.3}
            />
          </mesh>
          
          {/* Light bulb */}
          <pointLight 
            position={[0, 0.15, 0]} 
            intensity={10} 
            distance={1.5} 
            color={"#fff9c4"} 
            decay={2}
          />
        </group>
      )}
      
      {/* For any other furniture type, use a basic box with better materials */}
      {!isDesk && !isChair && !isComputer && !isStorage && !isPlant && !isRug && !isLamp && (
        <mesh castShadow>
          <boxGeometry args={[0.5, 0.5, 0.5]} />
          <meshStandardMaterial 
            color={color || "#a1887f"} 
            roughness={0.6} 
            metalness={0.1}
          />
        </mesh>
      )}
    </group>
  );
};

export default FurnitureItem;
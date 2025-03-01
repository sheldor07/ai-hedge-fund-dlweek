import React from 'react';
import { Html } from '@react-three/drei';
import { useDispatch } from 'react-redux';
import { setCurrentView } from '../store/simulationSlice';

interface ComputerScreenProps {
  position: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
}

const ComputerScreen: React.FC<ComputerScreenProps> = ({ 
  position, 
  rotation = [0, 0, 0], 
  scale = 1 
}) => {
  const dispatch = useDispatch();
  
  return (
    <group 
      position={position} 
      rotation={rotation as any}
      scale={[scale, scale, scale]}
    >
      {/* Computer base/stand */}
      <mesh position={[0, -0.5, 0]}>
        <boxGeometry args={[1.5, 0.1, 1]} />
        <meshStandardMaterial color="#444" />
      </mesh>
      
      {/* Computer stand */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[0.2, 1, 0.2]} />
        <meshStandardMaterial color="#555" />
      </mesh>
      
      {/* Computer screen frame */}
      <group position={[0, 1, 0]}>
        {/* Main frame */}
        <mesh>
          <boxGeometry args={[3, 2, 0.1]} />
          <meshStandardMaterial color="#263238" />
        </mesh>
        
        {/* Frame border */}
        <mesh position={[0, 0, 0.02]}>
          <boxGeometry args={[3.1, 2.1, 0.05]} />
          <meshStandardMaterial color="#4caf50" emissive="#4caf50" emissiveIntensity={0.5} />
        </mesh>
        
        {/* Screen inner border */}
        <mesh position={[0, 0, 0.06]}>
          <boxGeometry args={[2.8, 1.8, 0.01]} />
          <meshStandardMaterial color="#333" />
        </mesh>
      </group>
      
      {/* Interactive area to click - with pulsing effect */}
      <group position={[0, 1, 0.06]}>
        {/* Screen content preview */}
        <mesh 
          onClick={() => dispatch(setCurrentView('knowledgeBase'))}
        >
          <planeGeometry args={[2.8, 1.8]} />
          <meshBasicMaterial color="#071e26" opacity={0.9} transparent />
        </mesh>
        
        {/* Call-to-action text */}
        <mesh position={[0, 0, 0.01]}>
          <planeGeometry args={[2, 0.6]} />
          <meshStandardMaterial 
            color="#4caf50" 
            opacity={0.9} 
            transparent 
            emissive="#4caf50"
            emissiveIntensity={0.8}
          />
        </mesh>
        
        <Html
          transform
          position={[0, 0, 0.02]}
          scale={[0.02, 0.02, 0.02]}
          style={{
            width: '400px',
            height: '100px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            pointerEvents: 'none',
          }}
        >
          <div style={{
            color: 'white',
            fontWeight: 'bold',
            fontSize: '24px',
            textAlign: 'center',
            fontFamily: 'Arial, sans-serif',
            textShadow: '0 0 10px rgba(76, 175, 80, 0.8)',
            cursor: 'pointer',
          }}>
            <div>CLICK TO VIEW</div>
            <div style={{ marginTop: '5px', fontSize: '18px' }}>S&P COMPANIES KNOWLEDGE BASE</div>
          </div>
        </Html>
      </group>
    </group>
  );
};

export default ComputerScreen;
import React, { Suspense, useEffect } from 'react';
import './App.css';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from './store';
import { pauseSimulation } from './store/simulationSlice';

// Components
import ActivityLog from './components/ActivityLog';
import PerformanceMetrics from './components/PerformanceMetrics';
import SimulationControls from './components/SimulationControls';
import CharacterDetails from './components/CharacterDetails';

// Scenes
import HedgeFundBuilding from './scenes/HedgeFundBuilding';

// Hooks
import useSimulationEngine from './hooks/useSimulationEngine';

// Lazy load character components to improve performance
const Character = React.lazy(() => import('./components/Character'));

function App() {
  const dispatch = useDispatch();
  
  // Start the simulation engine but initially paused
  useSimulationEngine();
  
  useEffect(() => {
    // Ensure simulation starts paused
    dispatch(pauseSimulation());
  }, [dispatch]);
  
  // Get characters from Redux store
  const characters = useSelector((state: RootState) => state.characters.characters);
  const focusedEntity = useSelector((state: RootState) => state.simulation.focusedEntity);
  const dayNightCycle = useSelector((state: RootState) => state.simulation.dayNightCycle);
  
  // Calculate ambient light intensity based on day/night cycle
  const ambientLightIntensity = 0.5 + Math.sin(dayNightCycle * Math.PI * 2) * 0.2;
  
  return (
    <div className="App">
      {/* 3D Canvas */}
      <Canvas
        shadows
        style={{ width: '100vw', height: '100vh' }}
        gl={{ antialias: true }}
      >
        <Suspense fallback={null}>
          {/* Isometric Camera - Using PerspectiveCamera with specific settings for true isometric look */}
          <PerspectiveCamera
            makeDefault
            position={[20, 20, 20]}
            fov={25}
            near={1}
            far={1000}
            zoom={1}
          />
          
          {/* Lighting */}
          <ambientLight intensity={ambientLightIntensity} />
          <directionalLight
            position={[10, 15, 10]}
            intensity={1.5}
            castShadow
            shadow-mapSize-width={1024}
            shadow-mapSize-height={1024}
            shadow-camera-far={50}
            shadow-camera-left={-20}
            shadow-camera-right={20}
            shadow-camera-top={20}
            shadow-camera-bottom={-20}
          />
          
          {/* Main scene */}
          <group rotation={[0, Math.PI / 4, 0]}>
            <HedgeFundBuilding />
            
            {/* Characters */}
            {characters.map((character) => (
              <Suspense key={character.id} fallback={null}>
                <Character character={character} />
              </Suspense>
            ))}
          </group>
          
          {/* Fixed OrbitControls - no rotation allowed for isometric view */}
          <OrbitControls 
            enablePan={true} 
            enableZoom={true} 
            enableRotate={true}
            target={[0, 0, 0]}
            maxZoom={2}
            minZoom={0.5}
          />
        </Suspense>
      </Canvas>
      
      {/* UI Overlays */}
      <ActivityLog />
      <PerformanceMetrics />
      <SimulationControls />
      
      {/* Character details when one is selected */}
      {focusedEntity.type === 'character' && <CharacterDetails />}
    </div>
  );
}

export default App;
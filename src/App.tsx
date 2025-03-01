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
import ComputerScreen from './components/ComputerScreen';
import Sidebar from './components/Sidebar';
import KnowledgeBase from './components/KnowledgeBase';
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
  const currentView = useSelector((state: RootState) => state.simulation.currentView);
  
  // Calculate ambient light intensity based on day/night cycle
  const ambientLightIntensity = 0.5 + Math.sin(dayNightCycle * Math.PI * 2) * 0.2;
  
  return (
    <div className="App">
      {/* Sidebar Navigation */}
      <Sidebar />
      
      {/* Office View */}
      {currentView === 'office' && (
        <>
        <Canvas
          shadows
          style={{ width: 'calc(100vw - 220px)', height: '100vh', marginLeft: '220px' }}
          gl={{ antialias: true, precision: "highp" }}
          dpr={[1, 2]}
        >
          <Suspense fallback={null}>
            {/* Isometric Camera */}
            <PerspectiveCamera
              makeDefault
              position={[100, 100, 100]}
              fov={35}
              near={20}
              far={1000}
              zoom={4.5}
            />
            
            {/* Enhanced lighting */}
            <ambientLight intensity={ambientLightIntensity * 0.7} />
            <directionalLight
              position={[15, 20, 15]}
              intensity={1.8}
              castShadow
              shadow-mapSize-width={1024}
              shadow-mapSize-height={1024}
              shadow-camera-far={50}
              shadow-camera-left={-20}
              shadow-camera-right={20}
              shadow-camera-top={20}
              shadow-camera-bottom={-20}
              shadow-bias={-0.001}
            />
            {/* Rim light for better edge definition */}
            <directionalLight
              position={[-15, 10, -15]}
              intensity={0.5}
              color="#b3e5fc"
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
              
              {/* No computer screen in office view anymore */}
            </group>
            
            {/* OrbitControls */}
            <OrbitControls 
              enablePan={false} 
              enableZoom={false} 
              enableRotate={false}
              target={[0, 0, 0]}
              maxZoom={2.5}
              minZoom={0.5}
              maxPolarAngle={Math.PI / 2.2}
              minPolarAngle={Math.PI / 4}
              dampingFactor={0.1}
              rotateSpeed={0.8}
            />
          </Suspense>
        </Canvas>
        <ActivityLog />
      <PerformanceMetrics />
      <SimulationControls />
              </>
      )}
      
      {/* Knowledge Base View - Direct render */}
      {currentView === 'knowledgeBase' && (
        <div className="knowledge-base-view" style={{ marginLeft: '220px', height: '100vh', overflow: 'auto' }}>
          <div className="knowledge-base-wrapper">
            <KnowledgeBase />
          </div>
        </div>
      )}
      
      {/* UI Overlays */}

      
      {/* Character details when one is selected */}
      {focusedEntity.type === 'character' && <CharacterDetails />}
    </div>
  );
}

export default App;
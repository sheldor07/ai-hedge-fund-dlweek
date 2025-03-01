import React, { Suspense, useEffect, useState } from 'react';
import './App.css';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from './store';
import { 
  pauseSimulation, 
  setInvestmentAmount, 
  setSimulationPeriod, 
  completeOnboarding,
  completeTutorial
} from './store/simulationSlice';

// Components
import ActivityLog from './components/ActivityLog';
import PerformanceMetrics from './components/PerformanceMetrics';
import SimulationControls from './components/SimulationControls';
import CharacterDetails from './components/CharacterDetails';
import ComputerScreen from './components/ComputerScreen';
import Sidebar from './components/Sidebar';
import KnowledgeBase from './components/KnowledgeBase';
import Portfolio from './components/Portfolio';
import AgentViewPanel from './components/AgentViewPanel';
import DailySummary from './components/DailySummary';
import LoadingScreen from './components/LoadingScreen';
import InvestmentModal from './components/InvestmentModal';
import TimePeriodModal from './components/TimePeriodModal';
import TutorialTooltip from './components/TutorialTooltip';
// Scenes
import HedgeFundBuilding from './scenes/HedgeFundBuilding';

// Hooks
import useSimulationEngine, { onDayComplete } from './hooks/useSimulationEngine';

// Lazy load character components to improve performance
const Character = React.lazy(() => import('./components/Character'));

function App() {
  const dispatch = useDispatch();
  
  // State for loading/onboarding
  const [isLoading, setIsLoading] = useState(true);
  const [showInvestmentModal, setShowInvestmentModal] = useState(false);
  const [showTimePeriodModal, setShowTimePeriodModal] = useState(false);
  
  // State for daily summary modal
  const [showDailySummary, setShowDailySummary] = useState(false);
  const [summaryDate, setSummaryDate] = useState<Date | null>(null);
  
  // State for tutorial tooltips
  const [currentTutorialStep, setCurrentTutorialStep] = useState(0);
  
  // Tutorial steps
  const tutorialSteps = [
    {
      id: 'timeControls',
      content: 'Use these controls to start the simulation and adjust speed.',
      position: { bottom: '100px', right: '10px' }
    },
    {
      id: 'activityLog',
      content: 'This log shows all character activities and market events.',
      position: { left: '250px', top: '10px' }
    },
    {
      id: 'characters',
      content: 'Click on characters to view their details and follow their activities.',
      position: { left: '50%', top: '50%' }
    }
  ];
  
  // Start the simulation engine but initially paused
  useSimulationEngine();
  
  // Check if onboarding is complete from Redux
  const onboardingComplete = useSelector((state: RootState) => state.simulation.onboardingComplete);
  
  useEffect(() => {
    // Ensure simulation starts paused
    dispatch(pauseSimulation());
    
    // Listen for day completion event
    const handleDayComplete = (event: Event) => {
      const customEvent = event as CustomEvent;
      // Only show summary for weekdays
      const date = customEvent.detail.date as Date;
      const day = date.getDay();
      if (day !== 0 && day !== 6) { // Not Saturday or Sunday
        setSummaryDate(date);
        setShowDailySummary(true);
      }
    };
    
    onDayComplete.addEventListener('dayComplete', handleDayComplete);
    
    // Start loading sequence
    if (!onboardingComplete) {
      // After loading completes, show investment modal
      setTimeout(() => {
        setIsLoading(false);
        setShowInvestmentModal(true);
      }, 5000); // Give some time for the loading animation
    }
    
    return () => {
      onDayComplete.removeEventListener('dayComplete', handleDayComplete);
    };
  }, [dispatch, onboardingComplete]);
  
  // Handler for investment amount selection
  const handleInvestmentSelected = (amount: number) => {
    dispatch(setInvestmentAmount(amount));
    setShowInvestmentModal(false);
    setShowTimePeriodModal(true);
  };
  
  // Handler for time period selection
  const handleTimePeriodSelected = (startDate: Date, endDate: Date) => {
    dispatch(setSimulationPeriod({ startDate, endDate }));
    dispatch(completeOnboarding());
    setShowTimePeriodModal(false);
    
    // Start tutorial
    setTimeout(() => {
      setCurrentTutorialStep(1);
    }, 1000);
  };
  
  // Handle tutorial progression
  const handleTutorialStepComplete = () => {
    if (currentTutorialStep < tutorialSteps.length) {
      setCurrentTutorialStep(currentTutorialStep + 1);
    } else {
      dispatch(completeTutorial());
    }
  };
  
  // Get data from Redux store
  const characters = useSelector((state: RootState) => state.characters.characters);
  const focusedEntity = useSelector((state: RootState) => state.simulation.focusedEntity);
  const dayNightCycle = useSelector((state: RootState) => state.simulation.dayNightCycle);
  const currentView = useSelector((state: RootState) => state.simulation.currentView);
  
  // Calculate ambient light intensity based on day/night cycle
  const ambientLightIntensity = 0.5 + Math.sin(dayNightCycle * Math.PI * 2) * 0.2;
  
  return (
    <div className="App" style={{ position: 'relative', isolation: 'isolate' }}>
      {/* Modal Overlay Container with highest z-index */}
      <div style={{ 
        position: 'fixed', 
        top: 0, 
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 10000 // Super high z-index
      }}>
        {/* Loading Screen */}
        {isLoading && !onboardingComplete && (
          <div style={{ pointerEvents: 'auto' }}>
            <LoadingScreen onLoadingComplete={() => setIsLoading(false)} />
          </div>
        )}
        
        {/* Investment Modal */}
        {!isLoading && showInvestmentModal && !onboardingComplete && (
          <div style={{ pointerEvents: 'auto' }}>
            <InvestmentModal 
              onNext={handleInvestmentSelected} 
              onCancel={() => setShowInvestmentModal(false)}
            />
          </div>
        )}
        
        {/* Time Period Modal */}
        {showTimePeriodModal && !onboardingComplete && (
          <div style={{ pointerEvents: 'auto' }}>
            <TimePeriodModal
              onComplete={handleTimePeriodSelected}
              onBack={() => {
                setShowTimePeriodModal(false);
                setShowInvestmentModal(true);
              }}
            />
          </div>
        )}
      </div>
      
      {/* Main App UI - Only shown when onboarding is complete 
          Note: we now completely skip rendering the 3D scene during onboarding to avoid any HTML leaking through */}
      {(onboardingComplete) && (
        <>
          {/* Sidebar Navigation */}
          <Sidebar />
          
          {/* Office View */}
          {currentView === 'office' && (
            <>
            <Canvas
              shadows
              style={{ 
                width: 'calc(100vw - 220px)', 
                height: '100vh', 
                marginLeft: '220px',
                position: 'relative',
                zIndex: 1 // Lower z-index for the 3D canvas
              }}
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
          
          {/* Portfolio View - Direct render */}
          {currentView === 'portfolio' && (
            <div className="portfolio-view" style={{ marginLeft: '220px', height: '100vh', overflow: 'auto' }}>
              <div className="portfolio-wrapper">
                <Portfolio />
              </div>
            </div>
          )}
          
          {/* UI Overlays */}
          
          {/* Character details when one is selected */}
          {focusedEntity.type === 'character' && <CharacterDetails />}
          
          {/* Agent View Panel when a room is selected */}
          <AgentViewPanel />
          
          {/* Daily Summary modal placed in its own stacking context */}
          <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 10000, pointerEvents: 'none' }}>
            {showDailySummary && summaryDate && (
              <div style={{ pointerEvents: 'auto' }}>
                <DailySummary 
                  date={summaryDate} 
                  onClose={() => setShowDailySummary(false)}
                />
              </div>
            )}
          </div>
          
          {/* Tutorial tooltips in their own stacking context */}
          <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 9500, pointerEvents: 'none' }}>
            {currentTutorialStep > 0 && currentTutorialStep <= tutorialSteps.length && (
              <div style={{ pointerEvents: 'auto', position: 'absolute', ...tutorialSteps[currentTutorialStep - 1].position }}>
                <TutorialTooltip
                  step={currentTutorialStep}
                  position={{}}
                  content={tutorialSteps[currentTutorialStep - 1].content}
                  onComplete={handleTutorialStepComplete}
                  autoClose={false}
                />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;
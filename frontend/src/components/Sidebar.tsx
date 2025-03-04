import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import { setCurrentView } from '../store/simulationSlice';

const Sidebar: React.FC = () => {
  const dispatch = useDispatch();
  const currentView = useSelector((state: RootState) => state.simulation.currentView);

  const menuItems = [
    { id: 'office', label: 'Office View', icon: '🏢' },
    { id: 'knowledgeBase', label: 'Knowledge Base', icon: '💻' },
    { id: 'portfolio', label: 'Portfolio', icon: '📊' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <img src="logo.png" className="sidebar-logo" alt="Herkshire Bathaway Logo" />
      </div>
      <div className="sidebar-menu">
        {menuItems.map((item) => (
          <div 
            key={item.id}
            className={`sidebar-item ${currentView === item.id ? 'active' : ''}`}
            onClick={() => dispatch(setCurrentView(item.id as 'office' | 'knowledgeBase' | 'portfolio'))}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
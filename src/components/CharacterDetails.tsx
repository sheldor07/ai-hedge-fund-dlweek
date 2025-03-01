import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const CharacterDetails: React.FC = () => {
  const focusedEntity = useSelector((state: RootState) => state.simulation.focusedEntity);
  const characters = useSelector((state: RootState) => state.characters.characters);
  
  // Find the focused character if one exists
  const character = focusedEntity.type === 'character' && focusedEntity.id
    ? characters.find(c => c.id === focusedEntity.id)
    : null;
  
  if (!character) {
    return null;
  }
  
  return (
    <div className="character-info visible">
      <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', display: 'flex', alignItems: 'center' }}>
        <div 
          style={{ 
            width: '15px', 
            height: '15px', 
            borderRadius: '50%', 
            backgroundColor: getCharacterColor(character.type),
            marginRight: '5px'
          }} 
        />
        {character.name} ({character.type})
      </h3>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Current State:</strong> {character.state}
        {character.currentTask && (
          <div><strong>Current Task:</strong> {character.currentTask}</div>
        )}
        <div><strong>Location:</strong> {character.currentRoom}</div>
      </div>
      
      <div style={{ marginBottom: '10px' }}>
        <h4 style={{ margin: '5px 0', fontSize: '14px' }}>Skills</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px', rowGap: '3px' }}>
          <div>Analysis:</div>
          <div>
            <div style={{ 
              width: `${character.skills.analysis * 100}%`, 
              height: '8px', 
              backgroundColor: '#4287f5',
              borderRadius: '4px'
            }} />
          </div>
          
          <div>Decision:</div>
          <div>
            <div style={{ 
              width: `${character.skills.decision * 100}%`, 
              height: '8px', 
              backgroundColor: '#f5a742',
              borderRadius: '4px'
            }} />
          </div>
          
          <div>Communication:</div>
          <div>
            <div style={{ 
              width: `${character.skills.communication * 100}%`, 
              height: '8px', 
              backgroundColor: '#42f54e',
              borderRadius: '4px'
            }} />
          </div>
          
          <div>Risk Assessment:</div>
          <div>
            <div style={{ 
              width: `${character.skills.risk * 100}%`, 
              height: '8px', 
              backgroundColor: '#f54242',
              borderRadius: '4px'
            }} />
          </div>
        </div>
      </div>
      
      {character.conversations.length > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <h4 style={{ margin: '5px 0', fontSize: '14px' }}>Recent Conversations</h4>
          <div style={{ maxHeight: '100px', overflowY: 'auto', fontSize: '12px' }}>
            {character.conversations
              .slice(-3) // Show only the last 3 conversations
              .reverse() // Show most recent first
              .map((conv, index) => (
                <div key={index} style={{ marginBottom: '5px', padding: '5px', backgroundColor: '#f5f5f5', borderRadius: '3px' }}>
                  <div style={{ fontSize: '10px', color: '#777' }}>
                    {new Date(conv.timestamp).toLocaleTimeString()}
                  </div>
                  <div>"{conv.content}"</div>
                </div>
              ))}
          </div>
        </div>
      )}
      
      <div>
        <h4 style={{ margin: '5px 0', fontSize: '14px' }}>Recent Activity</h4>
        <div style={{ maxHeight: '100px', overflowY: 'auto', fontSize: '12px' }}>
          {character.activityHistory.length === 0 ? (
            <div style={{ color: '#777' }}>No recent activity</div>
          ) : (
            character.activityHistory
              .slice(-5) // Show only the last 5 activities
              .reverse() // Show most recent first
              .map((activity, index) => (
                <div key={index} style={{ marginBottom: '3px' }}>• {activity}</div>
              ))
          )}
        </div>
      </div>
    </div>
  );
};

// Helper function to get color based on character type
const getCharacterColor = (type: string): string => {
  const colors: Record<string, string> = {
    analyst: '#4287f5',
    quant: '#42f54e',
    executive: '#f5a742',
    riskManager: '#f54242',
  };
  
  return colors[type] || '#aaaaaa';
};

export default CharacterDetails;
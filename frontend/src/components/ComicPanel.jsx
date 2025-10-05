import React from 'react';

const ComicPanel = ({ panel, isPreview = false }) => {
  const getCharacterTags = (text) => {
    const characters = [];
    if (text.toLowerCase().includes('jamie')) characters.push('jamie');
    if (text.toLowerCase().includes('kylee')) characters.push('kylee');
    return characters;
  };

  return (
    <div className={`panel-item ${isPreview ? 'preview-panel' : ''}`}>
      <div className="flex items-center mb-3">
        <div className="panel-number">
          {panel.panel}
        </div>
        <h3 className="panel-title ml-3">Panel {panel.panel}</h3>
      </div>
      
      {/* Scene Description */}
      <div className="narration mb-4">
        <strong>Scene:</strong> {panel.scene}
        {panel.mood && (
          <div className="text-sm mt-1 opacity-80">
            <strong>Mood:</strong> {panel.mood}
          </div>
        )}
      </div>
      
      {/* Character Actions */}
      {panel.character_actions && (
        <div className="mb-3">
          <div className="text-sm font-bold mb-1 text-gray-600">Actions:</div>
          <div className="text-sm bg-purple-100 p-2 rounded border-l-4 border-purple-400">
            {panel.character_actions}
          </div>
        </div>
      )}
      
      {/* Character Tags */}
      {getCharacterTags(panel.dialogue + ' ' + (panel.character_actions || '')).length > 0 && (
        <div className="mb-3">
          {getCharacterTags(panel.dialogue + ' ' + (panel.character_actions || '')).map((character) => (
            <span key={character} className={`character-tag ${character}`}>
              {character.charAt(0).toUpperCase() + character.slice(1)}
            </span>
          ))}
        </div>
      )}
      
      {/* Dialogue */}
      {panel.dialogue && (
        <div className="speech-bubble">
          {panel.dialogue}
        </div>
      )}
    </div>
  );
};

export default ComicPanel;
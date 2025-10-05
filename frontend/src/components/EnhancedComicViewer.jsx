import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EnhancedComicViewer = ({ comic, onNewStory }) => {
  const [downloading, setDownloading] = useState(false);
  
  if (!comic) return null;

  const handleDownloadPNG = async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`${API}/comics/${comic.id}/download`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${comic.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PNG:', error);
      alert('Failed to download comic. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const handleExportMarkdown = () => {
    const content = `# ${comic.title}\n\n${comic.panels.map((panel, index) => 
      `## Panel ${panel.panel}\n**Scene:** ${panel.scene}\n${panel.character_actions ? `**Actions:** ${panel.character_actions}\n` : ''}${panel.mood ? `**Mood:** ${panel.mood}\n` : ''}**Dialogue:** ${panel.dialogue}\n`
    ).join('\n')}`;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${comic.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="comic-title mb-4">{comic.title}</h1>
        <div className="flex justify-center space-x-4 mb-6 flex-wrap gap-2">
          <button
            onClick={onNewStory}
            className="comic-button secondary"
            data-testid="new-story-button"
          >
            ✨ Create New Story
          </button>
          <button
            onClick={handleDownloadPNG}
            disabled={downloading}
            className="comic-button"
            data-testid="download-png-button"
          >
            {downloading ? (
              <span className="flex items-center">
                <div className="comic-loading w-4 h-4 mr-2"></div>
                Generating PNG...
              </span>
            ) : (
              '🖼️ Download PNG'
            )}
          </button>
          <button
            onClick={handleExportMarkdown}
            className="comic-button secondary"
            data-testid="export-markdown-button"
          >
            📤 Export Markdown
          </button>
        </div>
        
        {/* Comic Info */}
        <div className="flex justify-center space-x-6 text-sm text-gray-600 mb-4">
          <span>🎨 Style: {comic.style}</span>
          <span>📱 Format: {comic.aspect_ratio}</span>
          <span>🗓️ {comic.panels.length} panels</span>
        </div>
      </div>
      
      {/* Comic Panels Grid */}
      <div className="panels-grid">
        {comic.panels.map((panel, index) => (
          <div key={index} className="panel-item enhanced-panel">
            <div className="flex items-center mb-3">
              <div className="panel-number">
                {panel.panel}
              </div>
              <h3 className="panel-title ml-3">Panel {panel.panel}</h3>
            </div>
            
            {/* AI Generated Image with Comic Overlays */}
            {panel.image_base64 && (
              <div className="panel-image-container mb-4">
                <img 
                  src={`data:image/png;base64,${panel.image_base64}`}
                  alt={`Panel ${panel.panel} artwork`}
                  className="panel-image"
                  data-testid={`panel-${panel.panel}-image`}
                />
                
                {/* Character Actions Overlay (top) */}
                {panel.character_actions && (
                  <div className="comic-action-overlay">
                    <strong>Action:</strong> {panel.character_actions}
                  </div>
                )}
                
                {/* Speech Bubble Overlay (bottom) */}
                {panel.dialogue && (
                  <div className="comic-speech-overlay">
                    {panel.dialogue}
                  </div>
                )}
              </div>
            )}
            
            {/* Character Tags */}
            <div className="mb-3">
              {(panel.dialogue.toLowerCase().includes('jamie') || 
                (panel.character_actions && panel.character_actions.toLowerCase().includes('jamie'))) && (
                <span className="character-tag jamie">Jamie</span>
              )}
              {(panel.dialogue.toLowerCase().includes('kylee') || 
                (panel.character_actions && panel.character_actions.toLowerCase().includes('kylee'))) && (
                <span className="character-tag kylee">Kylee</span>
              )}
            </div>
            
            {/* Scene Description (below image for reference) */}
            <div className="text-sm text-gray-600 mb-2">
              <strong>Scene:</strong> {panel.scene}
              {panel.mood && (
                <div className="mt-1">
                  <strong>Mood:</strong> {panel.mood}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Story Summary */}
      <div className="comic-panel mt-8">
        <h3 className="panel-title mb-3">📖 Original Story</h3>
        <div className="bg-gray-50 p-4 rounded-lg border">
          <p className="text-gray-700 leading-relaxed">{comic.story_text}</p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedComicViewer;
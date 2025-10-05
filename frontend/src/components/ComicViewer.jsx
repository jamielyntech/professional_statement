import React from 'react';
import ComicPanel from './ComicPanel';

const ComicViewer = ({ comic, onNewStory, onSaveComic }) => {
  if (!comic) return null;

  const handleExport = async () => {
    // Simple export functionality - could be enhanced with image generation
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
        <div className="flex justify-center space-x-4 mb-6">
          <button
            onClick={onNewStory}
            className="comic-button secondary"
            data-testid="new-story-button"
          >
            ✨ Create New Story
          </button>
          <button
            onClick={handleExport}
            className="comic-button"
            data-testid="export-comic-button"
          >
            📥 Export Comic
          </button>
        </div>
      </div>
      
      {/* Comic Panels Grid */}
      <div className="panels-grid">
        {comic.panels.map((panel, index) => (
          <ComicPanel 
            key={index} 
            panel={panel} 
          />
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

export default ComicViewer;
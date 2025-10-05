import React, { useState } from 'react';

const StoryInput = ({ onSubmit, isLoading }) => {
  const [story, setStory] = useState('');
  const [title, setTitle] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (story.trim()) {
      onSubmit({ story: story.trim(), title: title.trim() || 'Untitled Story' });
    }
  };

  const exampleStories = [
    "Jamie and Kylee discover a mystical portal in their grandmother's attic. As they step through, they find themselves in a magical realm where crystals float in the air and mythical creatures roam freely. They must find the Crystal of Wisdom to return home, but first they encounter a wise dragon who tests their courage and friendship.",
    "In the enchanted forest of Whisperwind, Jamie and Kylee search for the lost unicorn Stardust. Along their journey, they meet talking trees, solve riddles from mischievous fairies, and learn that true magic comes from believing in yourself and helping others.",
    "When the village's magical protection spell begins to fade, Jamie and Kylee must venture to the Shadowlands to retrieve the ancient Moonstone. They face their deepest fears and discover that their combined powers of light and shadow can overcome any darkness."
  ];

  const useExampleStory = (exampleStory) => {
    setStory(exampleStory);
  };

  return (
    <div className="comic-panel max-w-4xl mx-auto">
      <h2 className="comic-subtitle text-center mb-6">
        ✨ Create Your Mystical Story ✨
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-bold mb-2" htmlFor="title">
            Story Title (optional)
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="comic-input w-full"
            placeholder="Enter your story title..."
          />
        </div>
        
        <div>
          <label className="block text-sm font-bold mb-2" htmlFor="story">
            Your Story
          </label>
          <textarea
            id="story"
            value={story}
            onChange={(e) => setStory(e.target.value)}
            className="comic-input comic-textarea w-full"
            placeholder="Tell your mystical story here... Include characters like Jamie and Kylee for the best results!"
            required
            data-testid="story-input"
          />
        </div>
        
        <button
          type="submit"
          disabled={isLoading || !story.trim()}
          className="comic-button w-full disabled:opacity-50 disabled:cursor-not-allowed"
          data-testid="create-comic-button"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <div className="comic-loading mr-2"></div>
              Creating Your Comic...
            </span>
          ) : (
            '🎭 Create Comic Panels'
          )}
        </button>
      </form>
      
      {/* Example Stories */}
      <div className="mt-8">
        <h3 className="panel-title text-center mb-4">Need inspiration? Try these examples:</h3>
        <div className="space-y-3">
          {exampleStories.map((example, index) => (
            <div key={index} className="bg-white p-4 rounded-lg border-2 border-dashed border-gray-300 hover:border-purple-400 transition-colors cursor-pointer"
                 onClick={() => useExampleStory(example)}>
              <p className="text-sm text-gray-700 line-clamp-3">{example}</p>
              <button 
                type="button"
                className="text-xs text-purple-600 hover:text-purple-800 mt-2 font-bold"
              >
                📖 Use this story
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StoryInput;
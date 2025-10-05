import React, { useState } from 'react';

const EnhancedStoryInput = ({ onSubmit, isLoading }) => {
  const [story, setStory] = useState('');
  const [title, setTitle] = useState('');
  const [style, setStyle] = useState('Mystical Watercolor');
  const [aspectRatio, setAspectRatio] = useState('4:5');
  const [generateImages, setGenerateImages] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (story.trim()) {
      onSubmit({ 
        story: story.trim(), 
        title: title.trim() || 'Untitled Story',
        style,
        aspect_ratio: aspectRatio,
        generate_images: generateImages
      });
    }
  };

  const styles = [
    'Mystical Watercolor',
    'Fantasy Digital Art',
    'Anime Manga Style',
    'Classic Comic Book',
    'Dreamy Illustration'
  ];

  const aspectRatios = [
    { value: '4:5', label: '4:5 (Instagram)' },
    { value: '16:9', label: '16:9 (Widescreen)' },
    { value: '1:1', label: '1:1 (Square)' }
  ];

  const exampleStories = [
    {
      title: "The Crystal Portal Adventure",
      story: "Jamie and Kylee discover a glowing crystal portal in their grandmother's attic. As they step through, they find themselves in a magical realm where crystals float in the air and mythical creatures roam freely. They must find the Crystal of Wisdom to return home, but first they encounter a wise dragon who tests their courage and friendship."
    },
    {
      title: "The Enchanted Forest Quest", 
      story: "In the enchanted forest of Whisperwind, Jamie and Kylee search for the lost unicorn Stardust. Along their journey, they meet talking trees, solve riddles from mischievous fairies, and learn that true magic comes from believing in yourself and helping others."
    },
    {
      title: "The Shadow Realm Challenge",
      story: "When the village's magical protection spell begins to fade, Jamie and Kylee must venture to the Shadowlands to retrieve the ancient Moonstone. They face their deepest fears and discover that their combined powers of light and shadow can overcome any darkness."
    }
  ];

  const useExampleStory = (example) => {
    setTitle(example.title);
    setStory(example.story);
  };

  return (
    <div className="comic-panel max-w-4xl mx-auto">
      <h2 className="comic-subtitle text-center mb-6">
        ✨ Create Your Mystical Comic ✨
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title and Story */}
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-bold mb-2" htmlFor="title">
              Story Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="comic-input w-full"
              placeholder="Enter your mystical story title..."
              data-testid="title-input"
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
        </div>

        {/* Style and Format Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-bold mb-2" htmlFor="style">
              Art Style
            </label>
            <select
              id="style"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="comic-input w-full"
              data-testid="style-select"
            >
              {styles.map((styleOption) => (
                <option key={styleOption} value={styleOption}>
                  {styleOption}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-bold mb-2" htmlFor="aspect">
              Format
            </label>
            <select
              id="aspect"
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              className="comic-input w-full"
              data-testid="aspect-ratio-select"
            >
              {aspectRatios.map((ratio) => (
                <option key={ratio.value} value={ratio.value}>
                  {ratio.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* AI Image Generation Toggle */}
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="generate-images"
            checked={generateImages}
            onChange={(e) => setGenerateImages(e.target.checked)}
            className="w-5 h-5 text-pink-600 border-2 border-pink-300 rounded focus:ring-pink-500"
            data-testid="generate-images-toggle"
          />
          <label htmlFor="generate-images" className="text-sm font-bold text-gray-700">
            🎨 Generate AI artwork for panels (recommended)
          </label>
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
              {generateImages ? 'Creating Comic with AI Art...' : 'Creating Comic Panels...'}
            </span>
          ) : (
            '🎭 Create Comic with AI Art'
          )}
        </button>
      </form>
      
      {/* Example Stories */}
      <div className="mt-8">
        <h3 className="panel-title text-center mb-4">Need inspiration? Try these examples:</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {exampleStories.map((example, index) => (
            <div 
              key={index} 
              className="bg-white p-4 rounded-lg border-2 border-dashed border-gray-300 hover:border-purple-400 transition-colors cursor-pointer"
              onClick={() => useExampleStory(example)}
              data-testid={`example-story-${index}`}
            >
              <h4 className="font-bold text-purple-600 mb-2">{example.title}</h4>
              <p className="text-sm text-gray-700 line-clamp-3">{example.story.substring(0, 100)}...</p>
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

export default EnhancedStoryInput;
import React, { useState, useEffect } from 'react';
import './App.css';
import CharacterUpload from './components/CharacterUpload';
import EnhancedStoryInput from './components/EnhancedStoryInput';
import EnhancedComicViewer from './components/EnhancedComicViewer';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentComic, setCurrentComic] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [savedComics, setSavedComics] = useState([]);

  // Fetch saved comics on component mount
  useEffect(() => {
    fetchSavedComics();
  }, []);

  const fetchSavedComics = async () => {
    try {
      const response = await axios.get(`${API}/comics`);
      setSavedComics(response.data);
    } catch (error) {
      console.error('Error fetching saved comics:', error);
    }
  };

  const handleStorySubmit = async (storyData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API}/parse-story`, storyData);
      const newComic = {
        ...response.data,
        story_text: storyData.story
      };
      setCurrentComic(newComic);
      
      // Refresh saved comics list
      await fetchSavedComics();
    } catch (error) {
      console.error('Error creating comic:', error);
      setError('Failed to create comic. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewStory = () => {
    setCurrentComic(null);
    setError(null);
  };

  const loadSavedComic = (comic) => {
    setCurrentComic(comic);
  };

  return (
    <div className="App mystical-bg min-h-screen py-8 px-4">
      <div className="container mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="comic-title mb-4">
            🌙 Mystical Whispers Comics ✨
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Transform your stories into magical comic adventures! 
            Create enchanting tales with Jamie, Kylee, and mystical creatures.
          </p>
        </header>

        {/* Error Message */}
        {error && (
          <div className="comic-panel bg-red-50 border-red-400 text-red-700 mb-6 max-w-2xl mx-auto" data-testid="error-message">
            <p>⚠️ {error}</p>
          </div>
        )}

        {/* Main Content */}
        {!currentComic ? (
          <div>
            {/* Character Upload */}
            <CharacterUpload />
            
            {/* Enhanced Story Input */}
            <EnhancedStoryInput 
              onSubmit={handleStorySubmit} 
              isLoading={isLoading} 
            />
            
            {/* Saved Comics */}
            {savedComics.length > 0 && (
              <div className="mt-12 max-w-4xl mx-auto">
                <h2 className="comic-subtitle text-center mb-6">
                  📖 Your Saved Comics
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {savedComics.map((comic) => (
                    <div 
                      key={comic.id}
                      className="comic-panel cursor-pointer hover:scale-105 transition-transform"
                      onClick={() => loadSavedComic(comic)}
                      data-testid={`saved-comic-${comic.id}`}
                    >
                      <h3 className="panel-title mb-2 truncate">{comic.title}</h3>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {comic.story_text}
                      </p>
                      <div className="flex justify-between items-center">
                        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                          {comic.panels.length} panels
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(comic.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <EnhancedComicViewer 
            comic={currentComic} 
            onNewStory={handleNewStory}
          />
        )}

        {/* Footer */}
        <footer className="text-center mt-16 text-sm text-gray-500">
          <div className="comic-panel max-w-2xl mx-auto">
            <p>
              ✨ Welcome to the magical world of Mystical Whispers Comics! ✨
            </p>
            <p className="mt-2">
              Create enchanting stories featuring brave adventurers like Jamie and Kylee 
              as they explore mystical realms, meet magical creatures, and discover the power of friendship.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
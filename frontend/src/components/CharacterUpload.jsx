import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CharacterUpload = ({ onUploadComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [characters, setCharacters] = useState([]);
  const [dragOver, setDragOver] = useState(null);

  const handleFileUpload = async (file, characterName) => {
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', characterName);

      const response = await axios.post(`${API}/upload-character?name=${characterName}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Refresh character list
      await fetchCharacters();
      if (onUploadComplete) onUploadComplete(response.data);
    } catch (error) {
      console.error('Error uploading character:', error);
      alert('Failed to upload character. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const fetchCharacters = async () => {
    try {
      const response = await axios.get(`${API}/characters`);
      setCharacters(response.data);
    } catch (error) {
      console.error('Error fetching characters:', error);
    }
  };

  React.useEffect(() => {
    fetchCharacters();
  }, []);

  const handleDrop = (e, characterName) => {
    e.preventDefault();
    setDragOver(null);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0], characterName);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDragEnter = (e, characterName) => {
    e.preventDefault();
    setDragOver(characterName);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(null);
  };

  const getCharacterImage = (characterName) => {
    const character = characters.find(c => c.name.toLowerCase() === characterName.toLowerCase());
    return character ? `data:image/png;base64,${character.image_base64}` : null;
  };

  return (
    <div className="comic-panel max-w-4xl mx-auto mb-8">
      <h2 className="comic-subtitle text-center mb-6">
        🎆 Character References 🎆
      </h2>
      <p className="text-center text-gray-600 mb-6">
        Upload reference photos for Jamie and Kylee to personalize your comic characters!
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Jamie Upload */}
        <div className="character-upload-card">
          <h3 className="panel-title text-center mb-4">Jamie</h3>
          <div
            className={`character-upload-zone ${
              dragOver === 'jamie' ? 'drag-over' : ''
            } ${getCharacterImage('jamie') ? 'has-image' : ''}`}
            onDrop={(e) => handleDrop(e, 'jamie')}
            onDragOver={handleDragOver}
            onDragEnter={(e) => handleDragEnter(e, 'jamie')}
            onDragLeave={handleDragLeave}
            data-testid="jamie-upload-zone"
          >
            {getCharacterImage('jamie') ? (
              <div className="uploaded-character">
                <img 
                  src={getCharacterImage('jamie')} 
                  alt="Jamie reference" 
                  className="character-preview"
                />
                <div className="character-overlay">
                  <p className="text-white font-bold">Jamie ✓</p>
                  <p className="text-xs text-white opacity-75">Click or drag to replace</p>
                </div>
              </div>
            ) : (
              <div className="upload-placeholder">
                <div className="upload-icon">🖼️</div>
                <p className="upload-text">Drop Jamie's photo here</p>
                <p className="upload-subtext">or click to browse</p>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                if (e.target.files[0]) {
                  handleFileUpload(e.target.files[0], 'jamie');
                }
              }}
              className="file-input"
              disabled={uploading}
            />
          </div>
        </div>

        {/* Kylee Upload */}
        <div className="character-upload-card">
          <h3 className="panel-title text-center mb-4">Kylee</h3>
          <div
            className={`character-upload-zone ${
              dragOver === 'kylee' ? 'drag-over' : ''
            } ${getCharacterImage('kylee') ? 'has-image' : ''}`}
            onDrop={(e) => handleDrop(e, 'kylee')}
            onDragOver={handleDragOver}
            onDragEnter={(e) => handleDragEnter(e, 'kylee')}
            onDragLeave={handleDragLeave}
            data-testid="kylee-upload-zone"
          >
            {getCharacterImage('kylee') ? (
              <div className="uploaded-character">
                <img 
                  src={getCharacterImage('kylee')} 
                  alt="Kylee reference" 
                  className="character-preview"
                />
                <div className="character-overlay">
                  <p className="text-white font-bold">Kylee ✓</p>
                  <p className="text-xs text-white opacity-75">Click or drag to replace</p>
                </div>
              </div>
            ) : (
              <div className="upload-placeholder">
                <div className="upload-icon">🖼️</div>
                <p className="upload-text">Drop Kylee's photo here</p>
                <p className="upload-subtext">or click to browse</p>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                if (e.target.files[0]) {
                  handleFileUpload(e.target.files[0], 'kylee');
                }
              }}
              className="file-input"
              disabled={uploading}
            />
          </div>
        </div>
      </div>
      
      {uploading && (
        <div className="text-center mt-4">
          <div className="comic-loading mx-auto"></div>
          <p className="text-gray-600 mt-2">Uploading character...</p>
        </div>
      )}
    </div>
  );
};

export default CharacterUpload;
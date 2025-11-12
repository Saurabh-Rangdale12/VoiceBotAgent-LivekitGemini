import { useState } from 'react';
import './App.css';
import Assistant from './components/Assistant';

// --- FEATURE 1: Define available models ---
const GEMINI_MODELS = [
  "gemini-2.0-flash-exp",
  "gemini-2.5-flash-native-audio-preview-09-2025",
  "gemini-2.5-flash-lite-preview-06-17",
];

function App() {
  const [showAssistant, setShowAssistant] = useState(false);
  const [selectedModel, setSelectedModel] = useState(GEMINI_MODELS[0]);

  return (
    <div className="app-container">
      <main>
        <section className="hero">
          <h1>Google Search Agent</h1>
          <p>Click the button below to start talking to the voice assistant.</p>
        </section>

        {/* --- FEATURE 1: Model Selection Dropdown --- */}
        <div className="model-selector">
          <label htmlFor="model-select">Choose a model: </label>
          <select
            id="model-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {GEMINI_MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>

        <button className="start-button" onClick={() => setShowAssistant(true)}>
          🎙️ Talk to Agent
        </button>
      </main>

      {/* --- FEATURE 1: Pass selected model to Assistant component --- */}
      {showAssistant && (
        <Assistant
          setShowAssistant={setShowAssistant}
          selectedModel={selectedModel}
        />
      )}
    </div>
  );
}

export default App;
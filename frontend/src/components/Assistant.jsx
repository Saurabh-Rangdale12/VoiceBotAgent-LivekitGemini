import { useState, useCallback, useEffect, useContext } from 'react';
import { LiveKitRoom, RoomAudioRenderer, RoomContext } from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';
import VoiceUI from './VoiceUI';
import MetricsDisplay from './MetricsDisplay'; // Import the new component

const RoomManager = ({ onDataReceived }) => {
  const room = useContext(RoomContext);
  useEffect(() => {
    if (room) {
      room.on(RoomEvent.DataReceived, onDataReceived);
      return () => {
        room.off(RoomEvent.DataReceived, onDataReceived);
      };
    }
  }, [room, onDataReceived]);
  return null;
};

export default function Assistant({ setShowAssistant, selectedModel }) {
  const [token, setToken] = useState(null);
  const [vadStatus, setVadStatus] = useState('SILENT');
  const [metrics, setMetrics] = useState(null); // State for the metrics object

  const getToken = useCallback(async () => {
    try {
      const response = await fetch(
        `http://localhost:5001/get-token?model=${encodeURIComponent(selectedModel)}`
      );
      const data = await response.json();
      setToken(data.token);
    } catch (error) {
      console.error("Error fetching token:", error);
    }
  }, [selectedModel]);

  useEffect(() => {
    getToken();
  }, [getToken]);

  const onDataReceived = useCallback((payload) => {
    const decoder = new TextDecoder();
    const message = JSON.parse(decoder.decode(payload));
    
    if (message.type === 'vad_update') {
      setVadStatus(message.status);
    } else if (message.type === 'metrics_update') {
      // Handle the new metrics message
      setMetrics(message.data);
    }
  }, []);

  if (!token) {
    return <div>Loading...</div>;
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <LiveKitRoom
          serverUrl={import.meta.env.VITE_LIVEKIT_URL}
          token={token}
          connect={true}
          video={false}
          audio={true}
          onDisconnected={() => setShowAssistant(false)}
        >
          {/* Main Content Wrapper */}
          <div className="assistant-wrapper">
            <div className="voice-ui-main">
              <RoomAudioRenderer />
              <VoiceUI vadStatus={vadStatus} />
            </div>
            {/* Render the new MetricsDisplay component */}
            <MetricsDisplay metrics={metrics} />
          </div>

          <RoomManager onDataReceived={onDataReceived} />
        </LiveKitRoom>
        
        <button className="disconnect-button" onClick={() => setShowAssistant(false)}>
          End Call
        </button>
      </div>
    </div>
  );
}
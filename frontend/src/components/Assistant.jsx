import { useState, useCallback, useEffect, useContext } from 'react';
import { LiveKitRoom, RoomAudioRenderer, RoomContext } from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';
import VoiceUI from './VoiceUI';
import MetricsDisplay from './MetricsDisplay'; // Import the new component

// This helper component is a good pattern and remains unchanged.
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
  
  // 1. Initialize metrics as an empty object and transcript as an empty string.
  const [metrics, setMetrics] = useState({});
  const [transcript, setTranscript] = useState('');

  // getToken function remains the same.
  const getToken = useCallback(async () => {
    try {
      const identity = `user-${Math.floor(Math.random() * 10000)}`;
      const room = "gemini-test-room";
      const url = `http://localhost:5001/get-token?identity=${encodeURIComponent(
        identity
      )}&room=${encodeURIComponent(room)}&model=${encodeURIComponent(selectedModel)}`;
      const response = await fetch(url);
      const data = await response.json();
      setToken(data.token);
    } catch (error) {
      console.error("Error fetching token:", error);
    }
  }, [selectedModel]);

  useEffect(() => {
    getToken();
  }, [getToken]);

  // 2. Revise the data handling logic to aggregate state.
  const onDataReceived = useCallback((payload) => {
    try {
      const decoder = new TextDecoder();
      const message = JSON.parse(decoder.decode(payload));

      console.log("📩 Data received:", message);

      if (message.type === "vad_update") {
        setVadStatus(message.status);
      } else if (message.type === "transcript_update") {
        // Handle transcript updates separately
        setTranscript(message.transcript);
      } else if (message.type === "metrics_update") {
        // Use the functional form of setState to merge new metrics
        // with the previous state.
        setMetrics(prevMetrics => ({
          ...prevMetrics,
          [message.metric_type]: message.data,
        }));
      }
    } catch (err)    { console.error("Error parsing incoming data:", err);
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
          <div className="assistant-wrapper">
            <div className="voice-ui-main">
              <RoomAudioRenderer />
              <VoiceUI vadStatus={vadStatus} />
            </div>
            {/* 3. Pass both metrics and transcript to the display component */}
            <MetricsDisplay metrics={metrics} transcript={transcript} />
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
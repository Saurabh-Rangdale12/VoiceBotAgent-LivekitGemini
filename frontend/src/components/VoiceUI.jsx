import {
  useVoiceAssistant,
  BarVisualizer,
  useTrackTranscription,
  useLocalParticipant,
} from '@livekit/components-react';
import { useEffect, useState } from 'react';

// --- Helper Components ---

const Message = ({ type, text }) => {
  return (
    <div className="message">
      <strong className={`message-type-${type}`}>
        {type === 'agent' ? 'Agent: ' : 'You: '}
      </strong>
      <span className="message-text">{text}</span>
    </div>
  );
};

const VadStatusIndicator = ({ status }) => {
  const isSpeaking = status === 'SPEAKING';
  return (
    <div className="vad-status">
      <span className={`vad-dot ${isSpeaking ? 'speaking' : 'silent'}`}></span>
      <span className="vad-text">{isSpeaking ? 'Agent is ' : 'Agent is '}{status.toLowerCase()}</span>
    </div>
  );
};


// --- Main UI Component ---

export default function VoiceUI({ vadStatus }) {
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant();
  const { localParticipant } = useLocalParticipant();
  const { segments: userTranscriptions } = useTrackTranscription(
    localParticipant.microphoneTrack
  );

  const [messages, setMessages] = useState([]);

  useEffect(() => {
    // Logic to combine and sort user and agent transcriptions by time
    const allMessages = [
      ...(agentTranscriptions?.map((t) => ({ ...t, type: 'agent' })) ?? []),
      ...(userTranscriptions?.map((t) => ({ ...t, type: 'user' })) ?? []),
    ].sort((a, b) => a.startTime - b.startTime);
    setMessages(allMessages);
  }, [agentTranscriptions, userTranscriptions]);

  return (
    <div className="voice-ui-container">
      <VadStatusIndicator status={vadStatus} />
      <BarVisualizer state={state} barCount={12} trackRef={audioTrack} />
      <div className="conversation-container">
        {messages.map((msg, index) => (
          <Message key={index} type={msg.type} text={msg.text} />
        ))}
      </div>
    </div>
  );
}
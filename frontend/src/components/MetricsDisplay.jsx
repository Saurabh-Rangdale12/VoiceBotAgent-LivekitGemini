import React from 'react';

// Helper to format timestamps nicely
const formatTimestamp = (ts) => {
  if (!ts) return 'N/A';
  try {
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
  } catch (e) {
    return 'Invalid Date';
  }
};

export default function MetricsDisplay({ metrics, transcript }) {
  // Destructure the metrics object for easier access
  const { vad, eou, llm, tts } = metrics;

  return (
    <div className="metrics-display-container">
      <h3>Agent Metrics</h3>

      {/* Transcript Metrics */}
      {transcript && (
        <div className="metric-group">
          <h4>Transcript</h4>
          <p>"{transcript}"</p>
        </div>
      )}

      {/* VAD Metrics */}
      {vad && (
        <div className="metric-group">
          <h4>VAD Metrics</h4>
          <p>Timestamp: {formatTimestamp(vad.timestamp)}</p>
        </div>
      )}

      {/* EOU Metrics */}
      {eou && (
        <div className="metric-group">
          <h4>EOU Metrics</h4>
          <p>End of Utterance Delay: {eou.end_of_utterance_delay?.toFixed(3)}s</p>
          <p>Transcription Delay: {eou.transcription_delay?.toFixed(3)}s</p>
          <p>Timestamp: {formatTimestamp(eou.timestamp)}</p>
        </div>
      )}

      {/* LLM Metrics */}
      {llm && (
        <div className="metric-group">
          <h4>LLM Metrics</h4>
          <p>TTFT: {llm.ttft?.toFixed(3)}s</p>
          <p>Total Tokens: {llm.total_tokens}</p>
          <p>Timestamp: {formatTimestamp(llm.timestamp)}</p>
        </div>
      )}

      {/* TTS Metrics */}
      {tts && (
        <div className="metric-group">
          <h4>TTS Metrics</h4>
          <p>TTFB: {tts.ttfb?.toFixed(3)}s</p>
          <p>Audio Duration: {tts.audio_duration?.toFixed(3)}s</p>
          <p>Start Time: {formatTimestamp(tts.timestamp)}</p>
        </div>
      )}
    </div>
  );
}
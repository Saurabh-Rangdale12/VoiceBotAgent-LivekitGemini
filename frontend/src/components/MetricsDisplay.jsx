import React from 'react';

// Helper to format timestamps and durations
const formatTime = (timestamp) => new Date(timestamp * 1000).toLocaleTimeString();
const formatDuration = (seconds) => `${seconds.toFixed(3)}s`;

const MetricBlock = ({ title, data, formatters = {} }) => {
  // Don't render the block if there's no data
  if (!data || Object.keys(data).length === 0) return null;
  
  return (
    <div className="metric-block">
      <h3>{title}</h3>
      {Object.entries(data).map(([key, value]) => {
        if (value === null || value === undefined) return null;
        // Convert camelCase to Title Case
        const displayKey = key.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase());
        const displayValue = formatters[key] ? formatters[key](value) : value.toString();
        return (
          <p key={key}>
            <strong>{displayKey}:</strong> {displayValue}
          </p>
        );
      })}
    </div>
  );
};

export default function MetricsDisplay({ metrics }) {
  // THE FIX: Check if metrics or metrics.llm exist before trying to render.
  if (!metrics || !metrics.llm) {
    return (
      <div className="metrics-container placeholder">
        <p>Waiting for first user utterance to collect metrics...</p>
      </div>
    );
  }

  return (
    <div className="metrics-container">
      {/* Conditionally render blocks based on available data */}
      {metrics.transcript && <MetricBlock title="Last Transcript Metrics" data={{ Transcript: metrics.transcript }} />}
      
      {metrics.vad && <MetricBlock
        title="VAD Metrics"
        data={metrics.vad}
        formatters={{ timestamp: formatTime }}
      />}
      
      {metrics.eou && <MetricBlock
        title="EOU Metrics"
        data={metrics.eou}
        formatters={{
          end_of_utterance_delay: formatDuration,
          transcription_delay: formatDuration,
          timestamp: formatTime,
        }}
      />}
      
      {/* This is the block that will be rendered by our RealtimeModel */}
      {metrics.llm && <MetricBlock
        title="LLM Metrics"
        data={metrics.llm}
        formatters={{ ttft: formatDuration, total_latency: formatDuration, timestamp: formatTime }}
      />}
      
      {metrics.tts && <MetricBlock
        title="TTS Metrics"
        data={metrics.tts}
        formatters={{
          ttfb: formatDuration,
          audio_duration: formatDuration,
          start_time: formatTime,
        }}
      />}
    </div>
  );
}
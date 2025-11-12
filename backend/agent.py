import logging
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, MetricsCollectedEvent
from livekit.agents import metrics as agent_metrics  # Import metrics module
from livekit.plugins import google
from livekit.plugins import silero
# from livekit.plugins.google import GoogleSearch

from prompts import INSTRUCTIONS, WELCOME_MESSAGE

# ----------------- Setup Logger -----------------
logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv(".env")

# ----------------- Agent Class -----------------
class SearchAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)

# ----------------- Entrypoint -----------------
async def entrypoint(ctx: JobContext):
    logger.info("🚀 Entrypoint called — new job received!")

    participant = ctx.job.participant
    model_name = "gemini-2.5-flash-lite-preview-06-17"

    if participant:
        logger.info(f"Participant metadata: {participant.metadata}")
        if participant.metadata:
            try:
                metadata = json.loads(participant.metadata)
                model_name = metadata.get("model", model_name)
                logger.info(f"Using LLM model from metadata: {model_name}")
            except json.JSONDecodeError:
                logger.warning("Could not decode participant metadata")
        else:
            logger.warning("Participant metadata is empty, using default model.")
    else:
        logger.warning("No participant found, using default model.")

    # ----------------- Initialize VAD -----------------
    vad = silero.VAD.load(force_cpu=True)
    vad.update_options(
        min_speech_duration=0.3,
        min_silence_duration=1.0,
        prefix_padding_duration=0.5,
        max_buffered_speech=60.0,
        activation_threshold=0.5,
    )

    # ----------------- Initialize Agent Session -----------------
    session = AgentSession(
        vad=vad,
        stt=google.STT(),
        # llm=google.LLM(model=model_name),
        llm=google.LLM(
            model=model_name,
            gemini_tools="google_search"  # Enable the Google Search tool
        ),
        tts=google.TTS(),
    )

    # ----------------- Initialize Usage Collector -----------------
    usage_collector = agent_metrics.UsageCollector()

    # ----------------- Helper to format timestamps -----------------
    def format_timestamp(ts: float) -> str:
        try:
            t = datetime.fromtimestamp(ts / 1000.0)
            return t.strftime("%H:%M:%S.%f")[:-3]
        except:
            return str(ts)

    # ----------------- Event Handlers -----------------
    async def on_vad_state_changed(event):
        try:
            data_to_send = json.dumps({"type": "vad_update", "status": event.state.name})
            await ctx.room.local_participant.publish_data(data_to_send)
            logger.info(f"🎤 VAD State Changed: {event.state.name}")
        except Exception as e:
            logger.error(f"Error in VAD handler: {e}")

    async def on_metrics_collected(event: MetricsCollectedEvent):
        try:
            metrics_obj = event.metrics
            
            if not metrics_obj:
                logger.debug("📊 Metrics object is None")
                return

            # Use the built-in log_metrics helper for formatted logging
            agent_metrics.log_metrics(metrics_obj, logger=logger)
            
            # Collect for usage summary
            usage_collector.collect(metrics_obj)

            # Build custom data structure for publishing
            data = {"type": "metrics_update"}
            
            # Check the type of metrics and extract relevant data
            if isinstance(metrics_obj, agent_metrics.STTMetrics):
                data["metric_type"] = "stt"
                data["data"] = {
                    "audio_duration": getattr(metrics_obj, "audio_duration", None),
                    "timestamp": getattr(metrics_obj, "timestamp", None),
                }
            
            elif isinstance(metrics_obj, agent_metrics.LLMMetrics):
                data["metric_type"] = "llm"
                data["data"] = {
                    "ttft": getattr(metrics_obj, "ttft", None),
                    "total_tokens": getattr(metrics_obj, "total_tokens", None),
                    "prompt_tokens": getattr(metrics_obj, "prompt_tokens", None),
                    "completion_tokens": getattr(metrics_obj, "completion_tokens", None),
                    "tokens_per_second": getattr(metrics_obj, "tokens_per_second", None),
                    "timestamp": getattr(metrics_obj, "timestamp", None),
                }
                logger.info("=" * 60)
                logger.info("🤖 LLM METRICS")
                logger.info(f"   TTFT: {getattr(metrics_obj, 'ttft', 0):.3f}s")
                logger.info(f"   Total Tokens: {getattr(metrics_obj, 'total_tokens', 0)}")
                logger.info(f"   Timestamp: {format_timestamp(getattr(metrics_obj, 'timestamp', 0))}")
                logger.info("=" * 60)
            
            elif isinstance(metrics_obj, agent_metrics.TTSMetrics):
                data["metric_type"] = "tts"
                data["data"] = {
                    "ttfb": getattr(metrics_obj, "ttfb", None),
                    "audio_duration": getattr(metrics_obj, "audio_duration", None),
                    "timestamp": getattr(metrics_obj, "timestamp", None),
                }
                logger.info("=" * 60)
                logger.info("🔊 TTS METRICS")
                logger.info(f"   TTFB: {getattr(metrics_obj, 'ttfb', 0):.3f}s")
                logger.info(f"   Audio Duration: {getattr(metrics_obj, 'audio_duration', 0):.3f}s")
                logger.info(f"   Timestamp: {format_timestamp(getattr(metrics_obj, 'timestamp', 0))}")
                logger.info("=" * 60)
            
            elif isinstance(metrics_obj, agent_metrics.VADMetrics):
                data["metric_type"] = "vad"
                data["data"] = {
                    "timestamp": getattr(metrics_obj, "timestamp", None),
                    "label": getattr(metrics_obj, "label", None),
                }
                # Change logger.info to logger.debug for these lines
                logger.debug("=" * 60)
                logger.debug("🎤 VAD METRICS")
                logger.debug(f"   Label: {getattr(metrics_obj, 'label', 'N/A')}")
                logger.debug(f"   Timestamp: {format_timestamp(getattr(metrics_obj, 'timestamp', 0))}")
                logger.debug("=" * 60)
            
            # Check for EOUMetrics (Pipeline version)
            elif hasattr(agent_metrics, 'PipelineEOUMetrics') and isinstance(metrics_obj, agent_metrics.PipelineEOUMetrics):
                data["metric_type"] = "eou"
                data["data"] = {
                    "end_of_utterance_delay": getattr(metrics_obj, "end_of_utterance_delay", None),
                    "transcription_delay": getattr(metrics_obj, "transcription_delay", None),
                    "timestamp": getattr(metrics_obj, "timestamp", None),
                }
                logger.info("=" * 60)
                logger.info("⏱️  EOU METRICS")
                logger.info(f"   End of Utterance Delay: {getattr(metrics_obj, 'end_of_utterance_delay', 0):.3f}s")
                logger.info(f"   Transcription Delay: {getattr(metrics_obj, 'transcription_delay', 0):.3f}s")
                logger.info(f"   Timestamp: {format_timestamp(getattr(metrics_obj, 'timestamp', 0))}")
                logger.info("=" * 60)

            # Publish to room
            await ctx.room.local_participant.publish_data(
                json.dumps(data),
                topic="agent_metrics"
            )
            
        except Exception as e:
            logger.error(f"Error in metrics handler: {e}", exc_info=True)

    async def on_user_transcript(event):
        try:
            transcript = event.transcript
            logger.info("=" * 60)
            logger.info("📝 USER TRANSCRIPT")
            logger.info(f'   "{transcript}"')
            logger.info("=" * 60)
            
            # Publish transcript
            data = {
                "type": "transcript_update",
                "transcript": transcript,
                "speaker": "user"
            }
            await ctx.room.local_participant.publish_data(
                json.dumps(data),
                topic="agent_metrics"
            )
        except Exception as e:
            logger.error(f"Error in transcript handler: {e}")

    async def on_agent_started_speaking(event):
        try:
            logger.info(f"🤖 Agent started speaking")
        except Exception as e:
            logger.error(f"Error in agent speaking handler: {e}")

    async def on_track_published(event):
        try:
            track = event.track
            participant = event.participant
            logger.info(f"🎶 New track published by {participant.identity}, kind: {track.kind}, name: {track.name}")
        except Exception as e:
            logger.error(f"Error in track published handler: {e}")

    # ----------------- Register Event Handlers -----------------
    session.on("vad_state_changed", lambda e: asyncio.create_task(on_vad_state_changed(e)))
    session.on("metrics_collected", lambda e: asyncio.create_task(on_metrics_collected(e)))
    session.on("user_transcript_committed", lambda e: asyncio.create_task(on_user_transcript(e)))
    session.on("agent_started_speaking", lambda e: asyncio.create_task(on_agent_started_speaking(e)))
    session.on("track_published", lambda e: asyncio.create_task(on_track_published(e)))

    # ----------------- Connect to Room -----------------
    await ctx.connect()

    # ----------------- Start Session -----------------
    await session.start(agent=SearchAssistant(), room=ctx.room)

    # ----------------- Send Welcome Message -----------------
    await session.say(WELCOME_MESSAGE)
    logger.info("✅ Agent session started and welcome message sent")
    
    # You can later get usage summary with:
    # summary = usage_collector.get_summary()
    # logger.info(f"Session Usage Summary: {summary}")


# ----------------- Run Worker -----------------
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
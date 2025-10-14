import logging
import json
import asyncio
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google, noise_cancellation
from google.genai import types

logger = logging.getLogger("agent")
load_dotenv(".env")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="")

async def entrypoint(ctx: JobContext):
    llm = google.beta.realtime.RealtimeModel(
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        voice="Puck",
        input_audio_transcription=types.RealtimeInputConfig(),
        instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice.
        Your responses are concise and friendly."""
    )
    session = AgentSession(llm=llm)

    async def on_user_transcript(event):
        data_to_send = json.dumps({
            "type": "user_transcript",
            "is_final": event.is_final,
            "text": event.transcript
        })
        await ctx.room.local_participant.publish_data(data_to_send)

    async def on_llm_chunk(event):
        data_to_send = json.dumps({
            "type": "agent_chunk",
            "text": event.chunk.text
        })
        await ctx.room.local_participant.publish_data(data_to_send)

    session.on("user_transcript", lambda event: asyncio.create_task(on_user_transcript(event)))
    session.on("llm_chunk", lambda event: asyncio.create_task(on_llm_chunk(event)))

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    await ctx.connect()
    # Iske aage koi ctx.run() nahi hai. Yeh sahi hai.

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
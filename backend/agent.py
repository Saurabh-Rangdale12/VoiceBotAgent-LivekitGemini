import logging
import json
import asyncio
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, MetricsCollectedEvent, llm
from livekit.plugins import google
from google.genai import types

from prompts import INSTRUCTIONS, WELCOME_MESSAGE

logger = logging.getLogger("agent")
load_dotenv(".env")

class SearchAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="")

async def entrypoint(ctx: JobContext):
    participant = ctx.job.participant
    model_name = "gemini-2.0-flash-exp"
    if participant and participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
            model_name = metadata.get("model", model_name)
            logger.info(f"Using model: {model_name}")
        except json.JSONDecodeError:
            logger.warning("Could not decode participant metadata")

    # The _gemini_tools parameter is removed for stability.
    llm_instance = google.beta.realtime.RealtimeModel(
        model=model_name,
        voice="Puck",
        instructions=INSTRUCTIONS
    )

    session = AgentSession(llm=llm_instance)

    # VAD State Handler - This is correct.
    async def on_vad_state_changed(event):
        data_to_send = json.dumps({
            "type": "vad_update",
            "status": event.state.name,
        })
        await ctx.room.local_participant.publish_data(data_to_send)

    # THE SECOND FIX: A robust metrics handler that works with RealtimeModel
    async def on_metrics_collected(event: MetricsCollectedEvent):
        metrics = event.metrics
        payload_data = {}

        # RealtimeModel provides simpler metrics under the 'llm' attribute.
        if hasattr(metrics, 'ttft'):
            payload_data["ttft"] = metrics.ttft
        if hasattr(metrics, 'total_latency'):
            payload_data["total_latency"] = metrics.total_latency
        if hasattr(metrics, 'timestamp'):
            payload_data["timestamp"] = metrics.timestamp
        
        if payload_data:
            payload = {"type": "metrics_update", "data": {"llm": payload_data}}

        await ctx.room.local_participant.publish_data(json.dumps(payload))

    session.on("vad_state_changed", lambda event: asyncio.create_task(on_vad_state_changed(event)))
    session.on("metrics_collected", lambda event: asyncio.create_task(on_metrics_collected(event)))

    await session.start(agent=SearchAssistant(), room=ctx.room)
    await ctx.connect()

    await asyncio.sleep(1)
    
    # THE FIRST FIX: The correct way to make a RealtimeModel speak
    # We create a new chat message from the assistant and then tell it to respond.
    # session.conversation.item.create(
    #     llm.ChatMessage(role="assistant", content=WELCOME_MESSAGE)
    # )
    # session.response.create()
    await session.say(WELCOME_MESSAGE)



if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
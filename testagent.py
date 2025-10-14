import asyncio
from livekit.agents import Worker, JobRequest, WorkerOptions
# Apne agent.py file se entrypoint function import karein
from agent import entrypoint

async def main():
    """
    Yeh script worker banati hai aur use seedha 'gemini-test-room'
    mein join karwa deti hai.
    """
    print("Starting agent worker...")

    # Worker ko sahi tarike se WorkerOptions ke saath initialize karein
    opts = WorkerOptions(entrypoint_fnc=entrypoint)
    worker = Worker(opts)

    print("Agent is now connecting to room 'gemini-test-room'...")
    # Ek job banayein aur use run karein.
    # Agent is room mein tab tak rahega jab tak job complete nahi hoti.
    await worker.run_job(JobRequest(room="gemini-test-room"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped.")
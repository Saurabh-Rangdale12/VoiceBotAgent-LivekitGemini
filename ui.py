import asyncio
import json
import os
import threading
from dotenv import load_dotenv
import streamlit as st
import sounddevice as sd
import numpy as np

from livekit import rtc
from livekit.api import AccessToken, VideoGrants

load_dotenv(".env")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")
KEYS_LOADED = LIVEKIT_URL and LIVEKIT_API_KEY and LIVEKIT_API_SECRET

st.set_page_config(page_title="LiveKit Voice Agent", page_icon="🎙️", layout="wide")

if "isconnected" not in st.session_state:
    st.session_state.isconnected = False
if "room" not in st.session_state:
    st.session_state.room = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "async_loop" not in st.session_state:
    st.session_state.async_loop = None
if "mic_stream" not in st.session_state:
    st.session_state.mic_stream = None

async def connect_and_run(loop):
    st.session_state.room = rtc.Room(loop=loop)
    room = st.session_state.room

    @room.on("data_received")
    def on_data_received(data: bytes, participant: rtc.RemoteParticipant):
        payload = json.loads(data.decode("utf-8"))
        if payload["type"] == "user_transcript":
            text, is_final = payload["text"], payload["is_final"]
            if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
                st.session_state.chat_messages[-1].update({"content": text, "is_final": is_final})
            else:
                st.session_state.chat_messages.append({"role": "user", "content": text, "is_final": is_final})
        elif payload["type"] == "agent_chunk":
            text = payload["text"]
            if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "assistant":
                st.session_state.chat_messages[-1]["content"] += text
            else:
                st.session_state.chat_messages.append({"role": "assistant", "content": text})
        st.rerun()

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("streamlit-user")
        .with_name("Streamlit User")
        .with_grants(VideoGrants(room="gemini-test-room", room_join=True))
        .to_jwt()
    )

    try:
        await room.connect(LIVEKIT_URL, token)
        st.session_state.isconnected = True
        st.rerun()
        audio_source = rtc.AudioSource(16000, 1)
        mic_track = rtc.LocalAudioTrack.create_audio_track("mic", audio_source)
        await room.local_participant.publish_track(mic_track)

        def callback(indata, frames, time, status):
            if status:
                print(status, flush=True)
            pcm_data = (indata * 32767).astype(np.int16)
            asyncio.run_coroutine_threadsafe(
                audio_source.capture_frame(pcm_data),
                loop
            )

        st.session_state.mic_stream = sd.InputStream(
            channels=1, samplerate=16000, dtype="float32", callback=callback)
        st.session_state.mic_stream.start()
        
        while room.isconnected:
            await asyncio.sleep(0.1)
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        st.session_state.isconnected = False
        st.rerun()
    finally:
        if st.session_state.mic_stream:
            st.session_state.mic_stream.stop()
            st.session_state.mic_stream.close()
            st.session_state.mic_stream = None

def run_async_in_thread(loop, coro_func):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coro_func(loop))

def start_connection():
    if not st.session_state.isconnected:
        loop = asyncio.new_event_loop()
        st.session_state.async_loop = loop
        threading.Thread(
            target=run_async_in_thread,
            args=(loop, connect_and_run),
            daemon=True,
        ).start()

def stop_connection():
    if st.session_state.isconnected and st.session_state.room:
        loop = st.session_state.async_loop
        future = asyncio.run_coroutine_threadsafe(
            st.session_state.room.disconnect(), loop)
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Error during disconnect: {e}")
        st.session_state.isconnected = False
        st.rerun()

st.title("🎙️ LiveKit Voice Agent (Gemini Integration)")
if not KEYS_LOADED:
    st.error("⚠️ LiveKit credentials not loaded. Please check your .env file.")
else:
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if msg["role"] == "user" and not msg.get("is_final", True):
                content += "..."
            st.markdown(content)
    if st.session_state.isconnected:
        if st.button("🔴 Disconnect"):
            stop_connection()
    else:
        if st.button("🟢 Connect and Speak"):
            start_connection()
            st.info("Connecting...")
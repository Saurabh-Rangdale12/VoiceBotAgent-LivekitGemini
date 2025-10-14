import os
import json # Import json
from livekit import api
from flask import Flask, request
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv(".env")
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/get-token")
def get_token():
    identity = request.args.get("identity", "default-user")
    room_name = request.args.get("room", "gemini-test-room")
    # --- FEATURE 1: Get model from request ---
    model = request.args.get("model", "gemini-2.5-flash-native-audio-preview-09-2025")

    # --- FEATURE 1: Create metadata to pass to the agent ---
    metadata = json.dumps({"model": model})

    token = api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")) \
        .with_identity(identity)\
        .with_name(identity)\
        .with_metadata(metadata)\
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name
        ))
    
    return {"token": token.to_jwt()}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
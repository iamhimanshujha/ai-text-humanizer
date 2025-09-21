# api-access.py
from fastapi import FastAPI, Body
from pydantic import BaseModel
import requests
import json

app = FastAPI(title="Conversantech Humanizer AI API Wrapper")

# Define request model
class HumanizerRequest(BaseModel):
    data: list
    event_data: dict = None
    fn_index: int
    trigger_id: int
    session_hash: str

# Endpoint to join queue
@app.post("/join_queue")
def join_queue(request_body: HumanizerRequest):
    join_url = "https://conversantech-humanizer-ai.hf.space/gradio_api/queue/join?__theme=system"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en-IN;q=0.9,en;q=0.8,hi-IN;q=0.7,hi;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://conversantech-humanizer-ai.hf.space",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://conversantech-humanizer-ai.hf.space/?__theme=system",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-fetch-storage-access": "active",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
        "x-zerogpu-uuid": "7g4FAwbU0BKeEo5dKGQNI"
    }

    response = requests.post(join_url, headers=headers, data=json.dumps(request_body.dict()))
    return response.json()

# Endpoint to get queue data
@app.get("/queue_data/{session_hash}")
def get_queue_data(session_hash: str):
    data_url = f"https://conversantech-humanizer-ai.hf.space/gradio_api/queue/data?session_hash={session_hash}"
    
    headers = {
        "accept": "text/event-stream",
        "accept-language": "en-US,en-IN;q=0.9,en;q=0.8,hi-IN;q=0.7,hi;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://conversantech-humanizer-ai.hf.space/?__theme=system",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-fetch-storage-access": "active",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"
    }

    response = requests.get(data_url, headers=headers, stream=True)
    # Collect the streaming response
    data_lines = []
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            data_lines.append(decoded_line)
    return {"stream_data": data_lines}


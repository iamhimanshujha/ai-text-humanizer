from fastapi import FastAPI, Query
from pydantic import BaseModel
import requests
import time

app = FastAPI(title="Humanizer AI API Access")

# Optional: define input model
class HumanizerRequest(BaseModel):
    text: str
    session_hash: str = "b4wvmtym1pr"  # default session hash
    fn_index: int = 0

HEADERS_JOIN = {
    "accept": "*/*",
    "accept-language": "en-US,en-IN;q=0.9,en;q=0.8,hi-IN;q=0.7,hi;q=0.6",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://conversantech-humanizer-ai.hf.space",
    "pragma": "no-cache",
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

HEADERS_DATA = HEADERS_JOIN.copy()
HEADERS_DATA["accept"] = "text/event-stream"

JOIN_URL = "https://conversantech-humanizer-ai.hf.space/gradio_api/queue/join?__theme=system"
DATA_URL = "https://conversantech-humanizer-ai.hf.space/gradio_api/queue/data"

@app.post("/humanize")
def humanize_text(request: HumanizerRequest):
    # Step 1: Join request
    payload_join = {
        "data": [request.text, "standard"],
        "event_data": None,
        "fn_index": request.fn_index,
        "trigger_id": 6,
        "session_hash": request.session_hash
    }
    join_response = requests.post(JOIN_URL, headers=HEADERS_JOIN, json=payload_join)
    join_json = join_response.json()
    print("Join Response:", join_json)

    # Step 2: Poll for result
    payload_data = {"session_hash": request.session_hash}
    final_response = None

    # Poll loop
    for _ in range(10):  # adjust retries as needed
        data_response = requests.post(DATA_URL, headers=HEADERS_DATA, json=payload_data)
        try:
            # Gradio returns multiple event lines, parse the last valid JSON
            lines = [line for line in data_response.text.splitlines() if line.strip().startswith("data:")]
            if lines:
                last_line = lines[-1][5:]  # remove "data:"
                final_response = last_line
                if "msg" not in final_response or "QUEUE" not in final_response:
                    break
        except Exception:
            pass
        time.sleep(1)

    return {"join": join_json, "result": final_response}

# api-access.py
from fastapi import FastAPI, Body, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Conversantech Humanizer AI API Wrapper")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# -----------------------
# CORS configuration
# -----------------------
allowed_origins = [
"*"  # replace with your frontend domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Allowed client IPs
# -----------------------
ALLOWED_IPS = ["123.45.67.89", "111.222.333.444"]  # replace with your allowed IPs

def check_ip(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail=f"Forbidden: Your IP ({client_ip}) is not allowed")

# -----------------------
# Request model
# -----------------------
class HumanizerRequest(BaseModel):
    data: list
    event_data: dict = None
    fn_index: int
    trigger_id: int
    session_hash: str

# -----------------------
# Common headers for Hugging Face API
# -----------------------
HEADERS = {
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

# -----------------------
# Join Queue Endpoint
# -----------------------
@app.post("/join_queue")
@limiter.limit("5/minute")
def join_queue(request: Request, request_body: HumanizerRequest):
    check_ip(request)
    join_url = "https://conversantech-humanizer-ai.hf.space/gradio_api/queue/join?__theme=system"
    
    try:
        response = requests.post(join_url, headers=HEADERS, data=json.dumps(request_body.dict()), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": "Failed to join queue", "details": str(e)}

# -----------------------
# Queue Data Endpoint
# -----------------------
@app.get("/queue_data/{session_hash}")
@limiter.limit("5/minute")
def get_queue_data(request: Request, session_hash: str):
    check_ip(request)
    data_url = f"https://conversantech-humanizer-ai.hf.space/gradio_api/queue/data?session_hash={session_hash}"
    
    try:
        response = requests.get(data_url, headers={**HEADERS, "accept": "text/event-stream"}, stream=True, timeout=10)
        response.raise_for_status()
        data_lines = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                data_lines.append(decoded_line)
        return {"stream_data": data_lines}
    except requests.RequestException as e:
        return {"error": "Failed to fetch queue data", "details": str(e)}

# -----------------------
# Health Check Endpoint
# -----------------------
@app.get("/health")
@limiter.limit("5/minute")
def health_check(request: Request):
    check_ip(request)
    return {"status": "ok", "message": "API wrapper is running"}

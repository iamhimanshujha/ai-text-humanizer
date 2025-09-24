# api-access.py
from fastapi import FastAPI, Body, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Minimal IP extraction function
def get_ip(request: Request):
    print("Request headers:", request.headers)
    ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    print("Resolved IP:", ip)
    return ip

# Initialize rate limiter
limiter = Limiter(key_func=get_ip)
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
# Request models
# -----------------------
class HumanizerRequest(BaseModel):
    data: list
    event_data: dict = None
    fn_index: int
    trigger_id: int
    session_hash: str

class ZeroGPTRequest(BaseModel):
    input_text: str

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
# ZeroGPT API headers
# -----------------------
ZEROGPT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en-IN;q=0.9,en;q=0.8,hi-IN;q=0.7,hi;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://www.zerogpt.com",
    "Pragma": "no-cache",
    "Referer": "https://www.zerogpt.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"'
}

ZEROGPT_COOKIES = "_gcl_au=1.1.2093563194.1758400573; _ga=GA1.1.1999342046.1758400574; _cc_id=800cdf58a21ce1d32f606f675d308da7; panoramaId_expiry=1759005379034; panoramaId=4e60b9d5ba4669be437dbecdcd6816d53938ef3a5a3af40137b6cffdf92e8b81; panoramaIdType=panoIndiv; _ga_0YHYR2F422=GS2.1.s1758478655$o2$g1$t1758480101$j60$l0$h1523464472; cto_bundle=wsfOll96b3czYjZ1bmlCeGVRZVdtUHJwck92Z3V1ZlA4ZUtnaFRPb3pmSHRJMnl1eng3eVM2OFJjUmJlVSUyQnlJZGtLNjN3dXU1bVAzc1B5SGJQRDlGeUJzcHFMcTlENG9YMDNOV0t5Z1psZjlPTms0NGV0UThscmdxdSUyRnNBSCUyQndhU09uWlp0dFNnNmhKVXM3cnZGZEdZVzE4TzMwbEtWb0Exa1M5WWhYU252OUtPaWJSdFRaRkg0WG55JTJCdjlXVXRHTFZESklFSDBCclVyNlBSNXRtZEFEYkdiTnclM0QlM0Q; __gads=ID=49ee81efad37e4f8:T=1758400578:RT=1758510250:S=ALNI_MY8DU4pQxuAD19WKqwADfxsEc-PJg; __gpi=UID=00001199123c0952:T=1758400578:RT=1758510250:S=ALNI_MYbsjWHrE2MAdfek86AbxGZXeUgyQ; __eoi=ID=8aba0271d780a3b2:T=1758400578:RT=1758510250:S=AA-AfjaEyBOp50t1G2nmfHwNTvrT; __qca=I0-1468342235-1758510448460"

# -----------------------
# Join Queue Endpoint
# -----------------------
@app.post("/join_queue")
@limiter.limit("5/minute")
def join_queue(request: Request, request_body: HumanizerRequest):
    # check_ip(request)
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
    # check_ip(request)
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
# ZeroGPT Test Endpoint
# -----------------------
@app.post("/zerogpt-test")
@limiter.limit("5/minute")
def zerogpt_test(request: Request, request_body: ZeroGPTRequest):
    zerogpt_url = "https://api.zerogpt.com/api/detect/detectText"
    
    # Prepare headers with cookies
    headers_with_cookies = ZEROGPT_HEADERS.copy()
    headers_with_cookies["Cookie"] = ZEROGPT_COOKIES
    
    try:
        response = requests.post(
            zerogpt_url, 
            headers=headers_with_cookies, 
            data=json.dumps({"input_text": request_body.input_text}), 
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": "Failed to detect text with ZeroGPT", "details": str(e)}

# -----------------------
# Health Check Endpoint
# -----------------------
@app.get("/health")
@limiter.limit("5/minute")
def health_check(request: Request):
    # check_ip(request)
    return {"status": "ok", "message": "API wrapper is running"}

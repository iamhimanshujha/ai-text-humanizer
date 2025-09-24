# Optimized for 500MB RAM - Render Free Tier
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
from collections import defaultdict

# Ultra-lightweight rate limiter (< 1KB memory per IP)
rate_limits = defaultdict(list)
RATE_LIMIT = 5  # requests per minute
WINDOW = 60  # 60 seconds

def check_rate_limit(ip: str) -> bool:
    now = time.time()
    # Clean old entries (automatic memory cleanup)
    rate_limits[ip] = [t for t in rate_limits[ip] if now - t < WINDOW]
    # Check limit
    if len(rate_limits[ip]) >= RATE_LIMIT:
        return False
    rate_limits[ip].append(now)
    return True

def get_ip(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()

app = FastAPI(title="AI Humanizer API", docs_url=None, redoc_url=None)  # Disable docs to save memory

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


# Lightweight request validation (no Pydantic to save memory)
def validate_humanizer_request(data: dict) -> bool:
    required = ['data', 'fn_index', 'trigger_id', 'session_hash']
    return all(key in data for key in required)

def validate_zerogpt_request(data: dict) -> bool:
    return 'input_text' in data and isinstance(data['input_text'], str)

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
async def join_queue(request: Request):
    # Rate limiting
    ip = get_ip(request)
    if not check_rate_limit(ip):
        raise HTTPException(429, "Rate limit exceeded. Try again in 1 minute.")
    
    # Parse request body manually (no Pydantic)
    try:
        body = await request.json()
        if not validate_humanizer_request(body):
            raise HTTPException(400, "Invalid request format")
    except:
        raise HTTPException(400, "Invalid JSON")
    
    try:
        response = requests.post(
            "https://conversantech-humanizer-ai.hf.space/gradio_api/queue/join?__theme=system",
            headers=HEADERS, 
            json=body,  # Use json parameter instead of data+dumps
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        raise HTTPException(500, "Service temporarily unavailable")

# -----------------------
# Queue Data Endpoint
# -----------------------
@app.get("/queue_data/{session_hash}")
def get_queue_data(request: Request, session_hash: str):
    # Rate limiting
    ip = get_ip(request)
    if not check_rate_limit(ip):
        raise HTTPException(429, "Rate limit exceeded. Try again in 1 minute.")
    
    try:
        response = requests.get(
            f"https://conversantech-humanizer-ai.hf.space/gradio_api/queue/data?session_hash={session_hash}",
            headers={**HEADERS, "accept": "text/event-stream"}, 
            stream=True, 
            timeout=10
        )
        response.raise_for_status()
        # Stream processing to save memory
        return {"stream_data": [line.decode("utf-8") for line in response.iter_lines() if line]}
    except requests.RequestException:
        raise HTTPException(500, "Service temporarily unavailable")

# -----------------------
# ZeroGPT Test Endpoint (Higher rate limit)
# -----------------------
@app.post("/zerogpt-test")
async def zerogpt_test(request: Request):
    # Higher rate limit for this endpoint (20/minute)
    ip = get_ip(request)
    now = time.time()
    rate_limits[f"{ip}_zerogpt"] = [t for t in rate_limits[f"{ip}_zerogpt"] if now - t < 60]
    if len(rate_limits[f"{ip}_zerogpt"]) >= 20:
        raise HTTPException(429, "Rate limit exceeded. Try again in 1 minute.")
    rate_limits[f"{ip}_zerogpt"].append(now)
    
    # Parse request body
    try:
        body = await request.json()
        if not validate_zerogpt_request(body):
            raise HTTPException(400, "Missing input_text field")
    except:
        raise HTTPException(400, "Invalid JSON")
    
    try:
        response = requests.post(
            "https://api.zerogpt.com/api/detect/detectText",
            headers={**ZEROGPT_HEADERS, "Cookie": ZEROGPT_COOKIES},
            json={"input_text": body["input_text"]},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        raise HTTPException(500, "ZeroGPT service unavailable")

# -----------------------
# Health Check Endpoint
# -----------------------
@app.get("/health")
def health_check(request: Request):
    # Rate limiting
   
    
    return {
        "status": "ok", 
        "memory_optimized": True,
        "rate_limits": "5/min general, 20/min zerogpt"
    }

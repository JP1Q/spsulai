import os
import json
from fastapi import FastAPI, HTTPException, Response, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel
from ipaddress import ip_address
import logging
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    model: str
    prompt: str

app = FastAPI()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

import firebase_admin
from firebase_admin import credentials, firestore


# FIREBASE STUFF MUHAHAHAHAHAHA NOW EVEN SAFE AND NOT HARDCODED FUNNY!

cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not cred_path or not os.path.exists(cred_path):
    raise ValueError("Firebase credentials path is not set or does not exist. which is bad :(")

cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred)
db = firestore.client()

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting configuration
RATE_LIMITS = "60/minute"  

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_api_key(
    api_key: str = Depends(api_key_header)
) -> dict:
    """Verify API key against Firebase users collection"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    # Check Firebase for valid API key
    users_ref = db.collection("users")
    query = users_ref.where("api_key", "==", api_key).limit(1)
    docs = query.stream()
    
    user_data = None
    for doc in docs:
        user_data = doc.to_dict()
        break
    
    if not user_data:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    # Check user access status
    if not user_data.get("access_enabled", True):
        raise HTTPException(
            status_code=403,
            detail="User account disabled"
        )
    
    return user_data

@app.post("/generate_response")
@limiter.limit(RATE_LIMITS)
async def generate_response(
    request: ChatRequest,
    fastapi_request: Request,
    user_data: dict = Depends(verify_api_key)
):
    """
    Endpoint to generate a streaming response from the Ollama API.
    Requires valid API key from Firebase.
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # Check classroom access
    classroom_ref = db.collection("classrooms").document(user_data["classroom"])
    classroom_data = classroom_ref.get().to_dict()
    if not classroom_data.get("access_enabled", True):
        raise HTTPException(
            status_code=403,
            detail="Classroom access disabled"
        )

    # URL of the Ollama API
    url = "http://host.docker.internal:11434/api/generate"

    payload = {
        "model": request.model,
        "prompt": request.prompt,
        "stream": True
    }

    async def generate():
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    yield f"Error: Received status code {response.status_code}\n"
                    return

                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"] + "\n"
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON Decode Error: {str(e)}")
                            yield f"JSON Decode Error: {str(e)}\n"
                        except Exception as e:
                            logger.error(f"Unexpected Error: {str(e)}")
                            yield f"Unexpected Error: {str(e)}\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  
        }
    )

@app.get("/models")
@limiter.limit(RATE_LIMITS)
async def list_models(
    request: Request,
    user_data: dict = Depends(verify_api_key)
):
    """
    Endpoint to list available Ollama models.
    Requires valid API key from Firebase.
    """
    url = "http://host.docker.internal:11434/api/tags"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch models: {response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Request error occurred: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error occurred: {str(e)}"
            )

# Add error handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return HTTPException(
        status_code=429,
        detail="Too many requests. Please try again later."
    )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
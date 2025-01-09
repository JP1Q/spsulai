import os
import json
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Dict, Any
from fastapi.responses import StreamingResponse
import asyncio
import httpx

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate_response")
def generate_response(request: Dict[str, Any]):
    """
    Endpoint to generate a streaming response from the Ollama API.
    """
    if not request.get('prompt'):
        raise HTTPException(status_code=400, detail="Prompt is required")

    url = "http://host.docker.internal:11434/api/generate"

    payload = {
        "model": request.get('model'),
        "prompt": request.get('prompt'),
        "stream": True
    }

    def generate():
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                yield f"Error: Received status code {response.status_code}\n"
                return

            for line in response.iter_lines():
                if line:
                    try:
                        # Decode and process each line
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            yield data["response"] + "\n"
                    except json.JSONDecodeError as e:
                        yield f"JSON Decode Error: {str(e)}\n"
                    except Exception as e:
                        yield f"Unexpected Error: {str(e)}\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Disables buffering in reverse proxies
        }
    )

@app.get("/models")
async def list_models():
    """
    Endpoint to list available Ollama models.
    """
    url = "http://host.docker.internal:11434/api/tags"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch models: {response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Request error occurred: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error occurred: {str(e)}"
            )

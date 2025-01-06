from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware
import json

# Create the FastAPI app
app = FastAPI()

# Allow CORS from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; you can specify allowed origins here
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define a model for the request body
class OllamaRequest(BaseModel):
    model: str
    prompt: str

# Define the Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"

@app.post("/generate_response")
async def generate_response(ollama_request: OllamaRequest):
    """
    Endpoint for conversation with AI
    """
    body = {
        "model": ollama_request.model,
        "prompt": ollama_request.prompt
    }

    complete_response = ""
    token_details = []
    total_tokens = 0
    eval_duration = 0
    tokens_per_second = 0

    # Use httpx to send an asynchronous POST request to the Ollama API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OLLAMA_URL, json=body, timeout=None)

            if response.status_code == 200:
                # Check if response is NDJSON
                if response.headers.get('Content-Type') == 'application/x-ndjson':
                    async for line in response.aiter_lines():
                        if line:
                            json_line = json.loads(line)
                            current_token = json_line.get("response", "")
                            complete_response += current_token

                            # Store token details
                            token_details.append(current_token)

                            # Update token statistics
                            if json_line.get("done", False):
                                total_tokens = json_line.get("prompt_eval_count", 0)
                                eval_duration = json_line.get("eval_duration", 1)
                                tokens_per_second = total_tokens / (eval_duration / 1e9)

                    # Prepare final output after completion
                    return {
                        "response": ''.join(token_details),
                        "total_tokens": total_tokens,
                        "tokens_per_second": f"{tokens_per_second:.2f}"
                    }
                else:
                    raise HTTPException(status_code=500, detail=f"Unexpected content type: {response.headers.get('Content-Type')}")
            else:
                raise HTTPException(status_code=response.status_code, detail="Ollama API request failed")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware

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
    Communicate with the Ollama API to generate a response based on the prompt.
    """
    body = {
        "model": ollama_request.model,
        "prompt": ollama_request.prompt
    }

    print(body) 

    # Use httpx to send an asynchronous POST request to the Ollama API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OLLAMA_URL, json=body)

            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("content", ""),
                    "tokens_used": data.get("tokens_used", "N/A"),
                    "generation_time": data.get("generation_time", "N/A")
                }
            else:
                raise HTTPException(status_code=response.status_code, detail="Ollama API request failed")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI()

# Configure CORS to allow requests from all origins (adjust origins for more control)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict access to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for login requests
class LoginRequest(BaseModel):
    username: str
    password: str

# Constants for Bakalari API
BAKALARI_LOGIN_URL = "https://spsul.bakalari.cz/api/login"
HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

@app.post("/verify_user")
async def verify_user(login_request: LoginRequest):
    """
    Verify user credentials with the Bakalari API.
    """
    body = {
        "client_id": "ANDR",
        "grant_type": "password",
        "username": login_request.username,
        "password": login_request.password,
    }

    # Use httpx.AsyncClient for API communication
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BAKALARI_LOGIN_URL, headers=HEADERS, data=body)

            if response.status_code == 200:  # Check for successful response
                data = response.json()
                return {
                    "message": "Login successful",
                    "access_token": data.get("access_token"),
                    "token_type": data.get("token_type", "N/A"),
                    "expires_in": data.get("expires_in", "N/A"),
                    "refresh_token": data.get("refresh_token", "N/A"),
                    "api_version": data.get("bak:ApiVersion", "N/A"),
                    "app_version": data.get("bak:AppVersion", "N/A"),
                }

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid username or password")

            raise HTTPException(
                status_code=response.status_code,
                detail=f"Login failed: {response.json().get('error_description', 'Unknown error')}",
            )
        except httpx.RequestError as exc:
            # Handle network or request-related errors
            raise HTTPException(
                status_code=500,
                detail=f"Request error: {exc}",
            )

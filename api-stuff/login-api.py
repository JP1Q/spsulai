from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI()

# Allow CORS from all origins (adjust the origins list for more specific control)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; for more control, you can specify specific domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define a model for the request body
class LoginRequest(BaseModel):
    username: str
    password: str

# Define the Bakalari API endpoint and headers
BAKALARI_LOGIN_URL = "https://spsul.bakalari.cz/api/login"
HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

@app.post("/verify_user")
async def verify_user(login_request: LoginRequest):
    """
    Verify user credentials with the Bakalari API.
    """
    # Prepare the body for the POST request
    body = {
        "client_id": "ANDR",
        "grant_type": "password",
        "username": login_request.username,
        "password": login_request.password
    }

    # Use httpx to send an asynchronous POST request
    async with httpx.AsyncClient() as client:
        try:
            # Send POST request to the Bakalari API
            response = await client.post(BAKALARI_LOGIN_URL, headers=HEADERS, data=body)

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    return {
                        "message": "Login successful",
                        "access_token": data["access_token"],
                        "token_type": data.get("token_type", "N/A"),
                        "expires_in": data.get("expires_in", "N/A"),
                        "refresh_token": data.get("refresh_token", "N/A"),
                        "api_version": data.get("bak:ApiVersion", "N/A"),
                        "app_version": data.get("bak:AppVersion", "N/A"),
                    }
                else:
                    raise HTTPException(status_code=500, detail="Unexpected response format")
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Login failed with status code {response.status_code}",
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

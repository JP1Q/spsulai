# Core and FastAPI
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# Web and HTTP
import httpx
from bs4 import BeautifulSoup

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Cryptography and Security
from cryptography.fernet import Fernet
from jwt import PyJWTError, encode, decode
from passlib.context import CryptContext
import secrets
import string
import status

# Date and Time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# System and Utilities
import logging
import psutil
import json

import asyncio

import os
import json
import dotenv
dotenv.load_dotenv()

# Type Hints
from typing import Optional, Dict, Union

# Nastavení logování
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



# Konfigurace
FERNET_KEY = os.getenv("FERNET_KEY").encode  
SECRET_KEY = os.getenv("SECRET_KEY")  
ALGORITHM = os.getenv("ALGORITHM", "HS256") 
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)  

# Inicializace šifrování
cipher = Fernet(FERNET_KEY)

# OAuth2 nastavení
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not cred_path or not os.path.exists(cred_path):
    raise ValueError("Firebase credentials path is not set or does not exist. which is bad :(")

cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred)
db = firestore.client()

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    # Add any other origins you need
]

app = FastAPI()

# Add this AFTER creating the app
# must come right after you create `app`
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # <-- your front-end origins
    allow_credentials=True,
    allow_methods=["*"],              # or explicitly ["GET","POST","OPTIONS",…]
    allow_headers=["*"],              # or ["Authorization","Content-Type",…]
    expose_headers=["*"],             # so your JS can read e.g. Authorization if you need it
)


# Modely dat
class LoginRequest(BaseModel):
    """Model pro přihlašovací údaje"""
    username: str
    password: str

class Classroom(BaseModel):
    """Model třídy z Bakalářů"""
    name: str
    access_enabled: bool = True  # Přístup povolen/vypnut
    teacher_id: str  # Učitel zodpovědný za třídu

class FirebaseUser(BaseModel):
    """Model uživatele v Firebase"""
    username: str
    classroom: str
    is_teacher: bool = False

# Pomocné funkce
async def store_auth_cookies(username: str, cookies: httpx.Cookies):
    """Uložení cookies do Firebase se šifrováním"""
    try:
        cookie_data = {
            'cookies': dict(cookies),
            'expires': (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        encrypted = cipher.encrypt(json.dumps(cookie_data).encode())
        
        db.collection("sessions").document(username).set({
            "cookies": encrypted,
            "updated": datetime.utcnow()
        })
    except Exception as e:
        logger.error(f"Chyba při ukládání cookies: {str(e)}")

async def get_auth_cookies(username: str) -> Optional[httpx.Cookies]:
    """Získání uložených cookies z Firebase"""
    try:
        doc = db.collection("sessions").document(username).get()
        if not doc.exists:
            return None
            
        data = doc.to_dict()
        decrypted = cipher.decrypt(data["cookies"]).decode()
        cookie_dict = json.loads(decrypted)
        
        cookies = httpx.Cookies()
        for name, value in cookie_dict["cookies"].items():
            cookies.set(name, value)
        return cookies
    except Exception as e:
        logger.error(f"Chyba při načítání cookies: {str(e)}")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT token and retrieve current user information."""
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        full_name: str = payload.get("full_name")  # Extracting full_name from the token payload
        if username is None or full_name is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return {"username": username, "full_name": full_name}
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

@app.post("/login")
async def login(login_request: LoginRequest):
    """Login endpoint that checks local credentials first, falls back to Bakaláři for new users"""
    try:
        # 1. First check if user exists locally
        user_query = db.collection("users").where("username", "==", login_request.username).limit(1)
        user_snapshot = user_query.get()
        user_data = user_snapshot[0].to_dict() if user_snapshot else None
        
        # 2. If user exists locally, verify password
        if user_data and "password_hash" in user_data:
            if verify_password(login_request.password, user_data["password_hash"]):
                # Generate new API key if none exists
                api_key = user_data.get("api_key", generate_api_key())
                if "api_key" not in user_data:
                    db.collection("users").document(user_data["full_name"]).update({
                        "api_key": api_key
                    })
                
                # Create fresh JWT token
                expiration = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_jwt_token(
                    username=user_data["full_name"],
                    classroom=user_data["classroom"],
                    is_admin=user_data.get("is_admin", False),
                    expires_delta=expiration
                )
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "api_key": api_key,
                    "user_info": {
                        "full_name": user_data["full_name"],
                        "classroom": user_data["classroom"],
                        "is_admin": user_data.get("is_admin", False),
                        "is_teacher": user_data.get("is_teacher", False)
                    }
                }
            else:
                # Password doesn't match for existing user
                raise HTTPException(
                    status_code=401,
                    detail="Neplatné uživatelské jméno nebo heslo"
                )
        
        # 3. If user doesn't exist locally, try Bakaláři authentication
        async with httpx.AsyncClient() as client:
            # Get initial cookies
            login_page = await client.get(
                "https://spsul.bakalari.cz/Login",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            cookies = login_page.cookies

            # Authenticate with Bakaláři
            bakalari_response = await client.post(
                "https://spsul.bakalari.cz/Login",
                data={
                    "username": login_request.username,
                    "password": login_request.password,
                    "returnUrl": ""
                },
                cookies=cookies,
                follow_redirects=True,
                timeout=10.0
            )

            # Check for failed login
            if "Přihlášení uživatele" in bakalari_response.text:
                raise HTTPException(
                    status_code=401,
                    detail="Neplatné uživatelské jméno nebo heslo"
                )

            # Parse user information from Bakaláři
            soup = BeautifulSoup(bakalari_response.text, "html.parser")
            lusername_element = soup.find("span", class_="lusername")
            lusername = lusername_element.get_text(strip=True) if lusername_element else login_request.username
            
            try:
                classroom_name, full_name = map(str.strip, lusername.split(',', 1))
            except ValueError:
                classroom_name = "unknown"
                full_name = lusername

            classroom_element = soup.find("span", class_="lclass")
            classroom = classroom_element.get_text(strip=True) if classroom_element else classroom_name

            # Store session cookies
            await store_auth_cookies(full_name, client.cookies)

            # Hash and store the password
            password_hash = pwd_context.hash(login_request.password)
            api_key = generate_api_key()

            # Create/update user in Firebase
            user_ref = db.collection("users").document(full_name)
            user_snapshot = user_ref.get()
            
            user_update = {
                "username": login_request.username,
                "password_hash": password_hash,
                "classroom": classroom,
                "last_login": datetime.now(ZoneInfo("Europe/Berlin")).isoformat(),
                "api_key": api_key,
                "bakalari_enabled": True
            }
            
            if not user_snapshot.exists:
                user_update.update({
                    "full_name": full_name,
                    "is_teacher": False,
                    "is_admin": False,
                    "last_login": datetime.now(ZoneInfo("Europe/Berlin")).isoformat(),
                })
            
            user_ref.set(user_update, merge=True)

            # Manage classroom data
            classroom_ref = db.collection("classrooms").document(classroom)
            classroom_ref.set({
                "name": classroom,
                "access_enabled": True,
                "teacher_id": "",
                "students": firestore.ArrayUnion([full_name])
            }, merge=True)

            # Check classroom access
            classroom_data = classroom_ref.get().to_dict()
            if not classroom_data or not classroom_data.get("access_enabled", True):
                raise HTTPException(
                    status_code=403,
                    detail="Přístup k této třídě je aktuálně vypnutý učitelem"
                )

            # Generate JWT token for new user
            expiration = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_jwt_token(
                username=full_name,
                classroom=classroom,
                is_admin=False,
                expires_delta=expiration
            )

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "api_key": api_key,
                "user_info": {
                    "full_name": full_name,
                    "classroom": classroom,
                    "is_admin": False,
                    "is_teacher": False
                }
            }

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Chyba spojení s Bakaláři: {str(e)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Vypršel časový limit spojení s Bakaláři"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chyba při přihlášení: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Vnitřní chyba serveru během přihlašování"
        )

@app.post("/toggle-classroom-access")
async def toggle_classroom(
    classroom: str, 
    enable: bool,
    current_user: str = Depends(get_current_user)
):
    """Povolení/zakázání přístupu pro celou třídu"""
    # Ověření, že uživatel je učitel této třídy
    user_ref = db.collection("users").document(current_user)
    user_data = user_ref.get().to_dict()
    
    classroom_ref = db.collection("classrooms").document(classroom)
    classroom_data = classroom_ref.get().to_dict()
    
    if not user_data.get("is_teacher") or classroom_data["teacher_id"] != current_user:
        raise HTTPException(status_code=403, detail="Pouze učitel této třídy může měnit nastavení")
    
    classroom_ref.update({"access_enabled": enable})
    return {"message": f"Přístup pro třídu {classroom} byl {'povolen' if enable else 'zakázán'}"}

@app.get("/class-students/{classroom}")
async def get_class_students(classroom: str, current_user: str = Depends(get_current_user)):
    """Získání seznamu studentů třídy z Bakalářů"""
    try:
        async with httpx.AsyncClient() as client:
            students_page = await client.get(
                f"https://spsul.bakalari.cz/Class/{classroom}/Students",
                cookies=await get_auth_cookies(current_user)
            )
            
            soup = BeautifulSoup(students_page.text, "html.parser")
            students_table = soup.find("table", class_="student-list")
            
            students = []
            for row in students_table.find_all("tr")[1:]:  # Přeskočit hlavičku
                cols = row.find_all("td")
                students.append({
                    "name": cols[0].text.strip(),
                    "email": cols[1].text.strip(),
                    "student_id": cols[2].text.strip()
                })
            
            return {"classroom": classroom, "students": students}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----- Llama AI Integration Endpoints -----
@app.get("/check_llama_version")
async def check_llama_version():
    """
    Check if a new version of Llama AI is available.
    This is a placeholder for integration with the Ollama API.
    """
    # TODO: Replace with actual API call to the Ollama service.
    
    return {"message": "Llama AI is up-to-date", "version": "1.0.0"}

@app.post("/update_ai")
async def update_ai():
    """
    Trigger an update of the AI.
    This is a placeholder for integration with the Ollama API.
    """
    # TODO: Replace with an API call that triggers the AI update via Ollama.
    return {"message": "AI update initiated. Check back later for status."}


@app.get("/server_status")
async def server_status():
    """
    Retrieve server status, including RAM usage, CPU usage, battery and power status.
    Uses psutil for system monitoring and hardware details.
    """
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    battery = psutil.sensors_battery() if psutil.sensors_battery() else None
    power_status = {
        "ram_usage": f"{ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB",
        "cpu_usage": f"{cpu}%",
         # Placeholder value for active users
    }
    
    if battery:
        power_status["battery_status"] = {
            "percent": f"{battery.percent}%",
            "plugged_in": battery.power_plugged,
            "time_left": str(timedelta(seconds=int(battery.secsleft))) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited"
        }
    else:
        power_status["battery_status"] = "Battery information not available"

    return power_status

# ----- Meta Llama Post Monitoring -----
async def fetch_latest_post_time():
    """
    Fetch the latest post time from the Meta Llama Hugging Face page.
    """
    url = "https://huggingface.co/meta-llama"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Request error: {exc}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        # Find the latest post date; adjust the selector as needed
        post_date_tag = soup.find("Current:")
        if post_date_tag:
            print()
        else:
            return None

async def check_for_new_posts():
    """
    Check for new posts on the Meta Llama Hugging Face page.
    """
    last_checked = datetime.now() - timedelta(days=1)  


# Teacher dashboard endpoints

@app.get("/teacher-classes")
async def get_teacher_classes(current_user: str = Depends(get_current_user)):
    """Get all classes taught by the current teacher"""
    try:
        # Verify user is a teacher
        user_ref = db.collection("users").document(current_user)
        user_data = user_ref.get().to_dict()
        
        if not user_data.get("is_teacher"):
            raise HTTPException(status_code=403, detail="Only teachers can access this endpoint")
        
        # Get classes where this user is the teacher
        classes_ref = db.collection("classrooms").where("teacher_id", "==", current_user)
        classes = [doc.to_dict() for doc in classes_ref.stream()]
        
        return {"classes": classes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/class-users/{classroom}")
async def get_class_users(classroom: str, current_user: str = Depends(get_current_user)):
    """Get all users in a specific classroom"""
    try:
        # Verify user is teacher of this class
        user_ref = db.collection("users").document(current_user)
        user_data = user_ref.get().to_dict()
        
        class_ref = db.collection("classrooms").document(classroom)
        class_data = class_ref.get().to_dict()
        
        if not user_data.get("is_teacher") or class_data["teacher_id"] != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to view this class")
        
        # Get all users in this class
        users = []
        for username in class_data.get("students", []):
            user_doc = db.collection("users").document(username).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                users.append({
                    "name": username,
                    "username": user_data.get("username"),
                    "last_login": user_data.get("last_login"),
                    "is_active": is_user_active(username)  # Helper function to check activity
                })
        
        return {"classroom": classroom, "users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/toggle-classroom-access")
async def toggle_classroom(
    classroom: str, 
    enable: bool,
    current_user: str = Depends(get_current_user)
):
    """Povolení/zakázání přístupu pro celou třídu"""
    # Ověření, že uživatel je učitel této třídy
    user_ref = db.collection("users").document(current_user)
    user_data = user_ref.get().to_dict()
    
    classroom_ref = db.collection("classrooms").document(classroom)
    classroom_data = classroom_ref.get().to_dict()
    
    if not user_data.get("is_teacher"):
        raise HTTPException(status_code=403, detail="Pouze učitel může měnit nastavení!")
    
    classroom_ref.update({"access_enabled": enable})

    if not enable:
        # Schedule re-enabling access after 100 minutes
        asyncio.create_task(restore_access_after_delay(classroom))

    return {"message": f"Přístup pro třídu {classroom} byl {'povolen' if enable else 'zakázán'}"}

# Helper function to check if user is active
def is_user_active(username: str) -> bool:
    """Check if user has been active recently (last 15 minutes)"""
    user_ref = db.collection("users").document(username)
    user_data = user_ref.get().to_dict()
    
    if not user_data or "last_login" not in user_data:
        return False
        
    last_login = datetime.fromisoformat(user_data["last_login"])
    return (datetime.utcnow() - last_login) < timedelta(minutes=15)



# Add these near your other utility functions
def create_jwt_token(username: str, classroom: str, is_admin: bool, expires_delta: datetime):
    """Helper to create JWT tokens"""
    return encode(
        {
            "sub": username,
            "class": classroom,
            "admin": is_admin,
            "exp": expires_delta
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def verify_password(plain_password: str, hashed_password: str):
    """Verify password against stored hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key(length=32):
    """Generate secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def restore_access_after_delay(classroom: str, delay: int = 6000):
    """Restores classroom access after the specified delay (100 minutes)."""
    await asyncio.sleep(delay)
    classroom_ref = db.collection("classrooms").document(classroom)
    classroom_ref.update({"access_enabled": True})


@app.get("/user/api_key")
async def get_user_api_key(authorization: str = Header(None)):
    try:
        # Extract token from Authorization header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        
        # Verify the token and get user info
        try:
            payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            # Get user data from database
            user_ref = db.collection("users").document(username)
            user_snapshot = user_ref.get()
            
            if not user_snapshot.exists:
                raise HTTPException(status_code=404, detail="User not found")
                
            user_data = user_snapshot.to_dict()
            api_key = user_data.get("api_key", generate_api_key())
            
            # Update API key if needed
            if "api_key" not in user_data:
                user_ref.update({"api_key": api_key})
                
            return {"api_key": api_key}
            
        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/rating")
async def put_user_rating(
    rating: int,
    authorization: str = Header(None),
):
    """
    Update the current user's rating.
    Expects:
    - rating: int query parameter
    - Authorization: Bearer <JWT>
    """
    # 1) Validate Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing/malformed Authorization header: %r", authorization)
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        # 2) Decode and validate JWT
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.warning("JWT payload missing 'sub': %r", payload)
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except PyJWTError as e:
        logger.warning("JWT decode error: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        # 3) Look up user by username field (not document ID)
        user_query = db.collection("users").where("full_name", "==", username).limit(1)
        results = user_query.get()
        if not results:
            logger.info("User not found for rating: %s", username)
            raise HTTPException(status_code=404, detail="User not found")
        
        user_ref = results[0].reference

        # 4) Perform the update
        user_ref.update({
            "rating": rating,
            # Optional: track last_rating_time
            "last_rating_at": datetime.utcnow().isoformat()
        })

        logger.info("Rating %s saved for user %s", rating, username)
        return {"message": "Rating updated successfully"}

    except HTTPException:
        # Re-raise our intended HTTP errors
        raise
    except Exception as e:
        # Catch anything unexpected
        logger.exception("Error updating rating for %s: %s", username, e)
        raise HTTPException(status_code=500, detail="Server error updating rating")
    

@app.get("/user/rating_get")
async def get_average_rating(authorization: str = Header(...)):
    # Extract and decode JWT
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Connect to Firestore
    db = firestore.client()
    users_ref = db.collection("users")
    docs = users_ref.stream()

    ratings = []
    for doc in docs:
        data = doc.to_dict()
        if "rating" in data:
            ratings.append(data["rating"])

    if not ratings:
        return {"average_rating": None, "multiplied": None}

    avg_rating = sum(ratings) / len(ratings)
    return {
        "average_rating": round(avg_rating, 2),
        "multiplied": round(avg_rating, 2)
    }
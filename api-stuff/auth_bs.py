from cryptography.fernet import Fernet
from httpx import Cookies
import json
from datetime import datetime, timedelta

# Initialize Fernet cipher
cipher = Fernet(SECRET_KEY[:43].encode())  # Fernet requires 32-byte key

async def store_auth_cookies(username: str, cookies: Cookies):
    """Store encrypted cookies in Firestore with expiration"""
    try:
        # Serialize and encrypt cookies
        cookie_data = {
            'cookies': dict(cookies),
            'expires_at': (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        encrypted_data = cipher.encrypt(json.dumps(cookie_data).encode())

        # Store in Firestore
        db.collection("auth_sessions").document(username).set({
            "cookies": encrypted_data,
            "user_agent": "BakalariAPI/1.0",
            "last_used": datetime.utcnow()
        })
    except Exception as e:
        print(f"Error storing cookies: {str(e)}")

async def get_auth_cookies(username: str) -> Optional[Cookies]:
    """Retrieve and decrypt stored cookies"""
    try:
        # Get from Firestore
        doc_ref = db.collection("auth_sessions").document(username)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None

        data = doc.to_dict()
        encrypted_data = data.get("cookies")
        
        if not encrypted_data:
            return None

        # Decrypt and verify expiration
        decrypted = json.loads(cipher.decrypt(encrypted_data).decode())
        if datetime.fromisoformat(decrypted['expires_at']) < datetime.utcnow():
            doc_ref.delete()
            return None

        # Convert back to Cookies object
        cookies = Cookies()
        for name, value in decrypted['cookies'].items():
            cookies.set(name, value, domain="spsul.bakalari.cz", path="/")
            
        return cookies

    except Exception as e:
        print(f"Error retrieving cookies: {str(e)}")
        return None
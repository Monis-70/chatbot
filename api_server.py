from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import secrets
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# Database setup (using simple JSON file for demonstration)
DB_FILE = "api_keys.json"

# Initialize database if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"keys": {}}, f)

app = FastAPI()

# API Key Security
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

class APIKeyData(BaseModel):
    key: str
    owner: str
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool = True
    rate_limit: int = 10  # Requests per minute

# Helper functions for key management
def generate_api_key(length=32):
    return secrets.token_urlsafe(length)

def save_key(key_data: Dict):
    with open(DB_FILE, "r+") as f:
        data = json.load(f)
        data["keys"][key_data["key"]] = key_data
        f.seek(0)
        json.dump(data, f, indent=4)

def get_key(key: str) -> Optional[Dict]:
    with open(DB_FILE, "r") as f:
        data = json.load(f)
        return data["keys"].get(key)

def revoke_key(key: str):
    with open(DB_FILE, "r+") as f:
        data = json.load(f)
        if key in data["keys"]:
            data["keys"][key]["is_active"] = False
            f.seek(0)
            json.dump(data, f, indent=4)

# Key generation endpoint
@app.post("/generate-key")
async def create_api_key(owner: str, expires_in_days: Optional[int] = None):
    """
    Generate a new API key for a user
    
    Parameters:
    - owner: Identifier for the key owner
    - expires_in_days: Optional expiration period
    
    Returns:
    - The generated API key (only shown once!)
    """
    key = generate_api_key()
    expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat() if expires_in_days else None
    
    key_data = {
        "key": key,
        "owner": owner,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "is_active": True,
        "rate_limit": 10
    }
    
    save_key(key_data)
    return {"api_key": key, "warning": "Save this key - it won't be shown again!"}

# Key validation middleware
async def validate_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API key missing")
    
    key_data = get_key(api_key)
    
    if not key_data:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    if not key_data["is_active"]:
        raise HTTPException(status_code=403, detail="API key revoked")
    
    if key_data["expires_at"] and datetime.fromisoformat(key_data["expires_at"]) < datetime.now():
        raise HTTPException(status_code=403, detail="API key expired")
    
    return key_data

# Protected endpoint example
@app.post("/chat")
async def protected_endpoint(request: Request, key_data: Dict = Depends(validate_api_key)):
    """
    Example protected endpoint that requires a valid API key
    """
    # Your existing chat logic here
    return {"message": "Access granted", "your_key_info": key_data}

# Admin endpoints
@app.get("/keys")
async def list_keys(admin_key: str = Depends(validate_api_key)):
    """List all keys (admin only)"""
    if key_data["owner"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    with open(DB_FILE, "r") as f:
        return json.load(f)

@app.post("/revoke-key/{key}")
async def revoke_api_key(key: str, admin_key: str = Depends(validate_api_key)):
    """Revoke a specific key (admin only)"""
    if key_data["owner"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    revoke_key(key)
    return {"status": "success", "message": f"Key {key} revoked"}
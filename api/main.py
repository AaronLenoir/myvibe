from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from datetime import datetime, timedelta
from jose import jwt
import uuid

app = FastAPI(title="Roster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://web:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key_for_dev")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")


@app.post("/auth/google")
async def auth_google(token: str):
    """Authenticate with Google OAuth token."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            user_data = response.json()

        user_id = str(uuid.uuid4())
        access_token = jwt.encode(
            {
                "user_id": user_id,
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("picture"),
                "exp": datetime.utcnow() + timedelta(minutes=30)
            },
            JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("picture")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Google auth failed")


@app.post("/auth/facebook")
async def auth_facebook(token: str):
    """Authenticate with Facebook OAuth token."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/v18.0/me",
                params={
                    "access_token": token,
                    "fields": "id,email,name,picture.type(large)"
                }
            )
            response.raise_for_status()
            user_data = response.json()

        # Get picture URL
        picture_url = None
        if "picture" in user_data:
            picture_data = user_data["picture"]
            if "data" in picture_data and "url" in picture_data["data"]:
                picture_url = picture_data["data"]["url"]

        user_id = str(uuid.uuid4())
        access_token = jwt.encode(
            {
                "user_id": user_id,
                "email": user_data.get("email", ""),
                "name": user_data.get("name", ""),
                "avatar_url": picture_url,
                "exp": datetime.utcnow() + timedelta(minutes=30)
            },
            JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.get("email", ""),
                "name": user_data.get("name", ""),
                "avatar_url": picture_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Facebook auth failed")


@app.get("/auth/me")
async def get_me(request: Request):
    """Get current user from JWT."""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token.split(" ")[1],
            JWT_SECRET,
            algorithms=["HS256"]
        )
        return {
            "id": payload.get("user_id"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "avatar_url": payload.get("avatar_url")
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"name": "Roster API", "version": "0.1.0"}

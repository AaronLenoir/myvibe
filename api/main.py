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
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")


@app.post("/auth/github")
async def auth_github(code: str):
    """Authenticate with GitHub OAuth code."""
    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                params={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            access_token = token_data.get("access_token")

            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()

        user_id = str(uuid.uuid4())
        jwt_token = jwt.encode(
            {
                "user_id": user_id,
                "email": user_data.get("email", ""),
                "name": user_data.get("name", user_data.get("login", "")),
                "avatar_url": user_data.get("avatar_url", ""),
                "exp": datetime.utcnow() + timedelta(minutes=30)
            },
            JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.get("email", ""),
                "name": user_data.get("name", user_data.get("login", "")),
                "avatar_url": user_data.get("avatar_url", "")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="GitHub auth failed")


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

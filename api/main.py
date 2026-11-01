import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
import httpx
import uuid
import datetime

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://roster.aaronlenoir.com",
        "https://api.roster.aaronlenoir.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://roster_user:roster_password@db:5432/roster")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Test database connection
@app.get("/test-db")
async def test_db():
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
        await conn.close()
        return {"status": "db_connected", "database_url": DATABASE_URL}
    except Exception as e:
        return {"status": "error", "error": str(e), "database_url": DATABASE_URL}

# GitHub OAuth
@app.get("/auth/github")
async def github_auth(request: Request):
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri=https://roster.aaronlenoir.com/auth/callback/github&scope=user:email"
    return RedirectResponse(url=github_auth_url)

@app.post("/auth/github")
async def github_callback(code: str):
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            data = response.json()
            access_token = data.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=400, detail="No access token received")
            
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_data = user_response.json()
            
            # Create JWT token
            token_data = {
                "sub": str(user_data.get("id")),
                "name": user_data.get("name", user_data.get("login")),
                "email": user_data.get("email", ""),
                "avatar": user_data.get("avatar_url", ""),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            }
            
            token = jwt.encode(token_data, JWT_SECRET, algorithm=ALGORITHM)
            
            return {"token": token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get current user
@app.get("/auth/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return {
            "id": payload.get("sub"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "avatar": payload.get("avatar")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

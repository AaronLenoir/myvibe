from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .config.settings import get_settings
from .config.database import database
from .routes import auth, teams, users, shift_types, periods, constraints, proposals
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Roster API",
    description="API for the Roster shift scheduling application",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
settings = get_settings()
cors_origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.auth_router)
app.include_router(teams.teams_router)
app.include_router(users.users_router)
app.include_router(shift_types.shift_types_router)
app.include_router(periods.periods_router)
app.include_router(constraints.constraints_router)
app.include_router(proposals.proposals_router)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": exc.errors(),
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc),
        },
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks."""
    logger.info("Starting Roster API...")
    
    # Initialize database (tables should already exist from init.sql)
    # But we can check and create them if needed
    try:
        await database.create_tables()
        logger.info("Database tables verified")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    logger.info("Roster API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Roster API...")
    await database.close()
    logger.info("Roster API shutdown complete")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "roster-api",
        "timestamp": "2024-01-01T00:00:00Z"  # Will be updated in production
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": "Roster API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

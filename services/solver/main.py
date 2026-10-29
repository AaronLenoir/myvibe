from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .schemas import ProblemData, ValidationData, SolveResponse, ValidateResponse
from .services.solver_service import solver_service
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
    title="Roster Solver",
    description="Solver service for the Roster shift scheduling application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware (allow requests from API service)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://api:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Solve endpoint
@app.post("/solve", response_model=SolveResponse, summary="Solve scheduling problem")
async def solve_problem(problem_data: ProblemData):
    """Solve a scheduling problem and return multiple proposals."""
    try:
        logger.info(f"Received solve request for period: {problem_data.period_id}")
        
        response = await solver_service.solve(problem_data)
        logger.info(f"Generated {len(response.proposals)} proposals")
        
        return response
    except Exception as e:
        logger.error(f"Solve failed: {e}")
        raise

# Validate endpoint
@app.post("/validate", response_model=ValidateResponse, summary="Validate roster")
async def validate_roster(validation_data: ValidationData):
    """Validate a roster against constraints."""
    try:
        logger.info(f"Received validation request for proposal: {validation_data.proposal_id}")
        
        response = await solver_service.validate(validation_data)
        logger.info(f"Validation completed: {len(response.violations)} violations found")
        
        return response
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "roster-solver",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": "Roster Solver",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

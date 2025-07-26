from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Import routers (after loading .env)
from .routers import process, files

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="trippleCheck",
    description="A multi-perspective AI agent application with an asynchronous pipeline.",
    version="1.0.0"
)

# Add rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Define the path to the static files directory (frontend assets)
static_files_dir = Path(__file__).parent / "static" / "dist"
api_app = FastAPI(title="API")

# Include routers in the API sub-application
api_app.include_router(process.router)
api_app.include_router(files.router)

# Mount the API sub-application under the /api/v1 prefix
app.mount("/api/v1", api_app)

# Add static file serving if the directory exists
if static_files_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_files_dir), html=True), name="static")

    @app.get("/", include_in_schema=False)
    @limiter.limit("60/minute")  # Limit homepage access
    async def serve_spa(request):
        """Serve the main HTML file of the SvelteKit application (Single Page Application)"""
        index_path = static_files_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend is not available")
else:
    # Fallback when the static files directory does not exist
    @app.get("/", tags=["General"])
    @limiter.limit("60/minute")  # Limit homepage access
    async def read_root(request):
        """Basic endpoint to check if the application is running."""
        return {"message": "API is running correctly. Frontend is not available."}

# CORS Configuration with more restrictive settings
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://pixel-pasta-ai-app.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to only needed methods
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

if __name__ == "__main__":
    # This block is usually not used directly,
    # the application is run via Uvicorn from the command line:
    # uvicorn fastapi_app.app.main:app --reload --host 0.0.0.0 --port 8000
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)

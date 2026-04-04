import time
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from utils.logger import logging as logger

from routes.auth import router as autentication_router
from routes.ai_recipe_generator import router as recipe_generator_router
from routes.user_recipes import router as user_recipes_router
from routes.community import router as community_recipe_router
from routes.user_own_recipe import router as user_own_recipe

# 1. App Configuration (Internal)
class AppConfig:
    """Global configuration for the FastAPI application."""
    TITLE: str = "NUtri Chef AI API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ALLOW_ORIGINS: list = ["*"]
    HOST: str = "0.0.0.0"
    PORT: int = 8000

# 2. Lifespan (Startup/Shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Event handler for application startup and shutdown events."""
    logger.info(f"Starting {AppConfig.TITLE} (v{AppConfig.VERSION})...")
    yield
    logger.info(f"Shutting down {AppConfig.TITLE}...")

# 3. Create FastAPI Instance
app = FastAPI(
    title=AppConfig.TITLE,
    version=AppConfig.VERSION,
    lifespan=lifespan,
    debug=AppConfig.DEBUG,
)

# 4. Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=AppConfig.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captures all unhandled exceptions and returns a structured JSON response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# Route Inclusion
app.include_router(autentication_router)

app.include_router(recipe_generator_router)

app.include_router(user_recipes_router)

app.include_router(community_recipe_router)

app.include_router(user_own_recipe)

# Basic Routes (Root & Health Check)
@app.get("/", tags=["Monitoring"])
async def root():
    return {
        "message": f"Welcome to the {AppConfig.TITLE}",
        "version": AppConfig.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Simple health check endpoint for monitoring purposes."""
    return {
        "status": "Healthy",
        "timestamp": time.time(),
        "version": AppConfig.VERSION
    }

# 8. Main Entrypoint
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Launching server on {AppConfig.HOST}:{AppConfig.PORT}")
    PORT = int(os.environ.get("PORT", 8000)) 
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=AppConfig.DEBUG)

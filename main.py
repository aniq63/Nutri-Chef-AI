from fastapi import FastAPI , requests
from database.connection import init_db
from routes import auth
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the FastAPI application.
    Handles startup and shutdown logic.
    """
    # Startup: Initialize database tables
    await init_db()
    yield
    # Shutdown: Clean up resources if needed


app = FastAPI(
    title="Nutri Chef AI",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint for API."""
    return {"message": "Nutri Chef AI API is running", "status": "healthy"}


# Include routers
app.include_router(auth.router)

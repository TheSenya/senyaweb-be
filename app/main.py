# main entry point of out application, when it all starts from

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings

from google import genai
from openrouter import OpenRouter

from app.core.db import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    This handles the startup and shutdown logic.
    """
    
    # Initialize DB (create tables)
    create_db_and_tables()
    """
    Lifespan context manager for the FastAPI application.
    This handles the startup and shutdown logic.
    """

    print("\n" + "=" * 50)
    print(f"🔧 Initializing connections")
    print("=" * 50)

    # Create the openrouter client
    print("🚀 Initializing OpenRouter client...")
    app.state.openrouter = OpenRouter(settings.OPENROUTER_KEY)
    print("✅ OpenRouter client initialized")

    # Create the gemini client
    print("🚀 Initializing Gemini client...")
    app.state.gemini = genai.Client(api_key=settings.GOOGLE_AI_STUDIO_API_KEY)
    print("✅ Gemini client initialized")

    print("=" * 50 + "\n")

    yield

    print("Shutting down...")

# --- App Initialization & Metadata ---
app = FastAPI(
    title = "Senya Web",
    description = "A site for myself to do the things I want",
    version = "0.0.1",
    lifespan=lifespan
)

from app.core.config import settings
from app.middleware.encryption import EncrpytionMiddleware
from app.middleware.logger import LoggingMiddleware

# Add logging middleware first (outermost) so it logs all requests
app.add_middleware(LoggingMiddleware)

app.add_middleware(EncrpytionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, # Allows origins only from the provided sources
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Allow all headers (Authorization, Content-Type)
)

from app.api.endpoints import auth
from app.api.endpoints import ai
app.include_router(auth.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"All is healthy and good"}
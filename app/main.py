# main entry point of out application, when it all starts from

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- App Initialization & Metadata ---
app = FastAPI(
    title = "Senya Web",
    description = "A site for myself to do the things I want",
    version = "0.0.1",
)

from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, # Allows origins only from the provided sources
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Allow all headers (Authorization, Content-Type)
)

from app.api.endpoints import auth
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"All is healthy and good"}
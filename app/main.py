# main entry point of out application, when it all starts from

from fastapi import FastAPI

# --- App Initialization & Metadata ---
app = FastAPI(
    title = "Senya Web",
    description = "A site for myself to do the things I want",
    version = "0.0.1",
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"], # Allow all HTTP methods (GET, POST, PUT, DELETE)
#     allow_headers=["*"], # Allow all headers (Authorization, Content-Type)
# )

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"All is healthy and good"}
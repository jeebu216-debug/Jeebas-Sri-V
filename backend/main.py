from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router


app = FastAPI(
    title="LegalEase API",
    version="1.0.0",
    description=(
        "AI-powered legal document drafting backend."
    )
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


app.include_router(router)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def root():

    return {
        "service": "LegalEase API",
        "status": "healthy",
        "message": "Backend is running."
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }
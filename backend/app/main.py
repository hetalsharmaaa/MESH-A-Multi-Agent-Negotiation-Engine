from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="MESH - Multi-Agent Negotiation Engine",
    description="AI-Driven Multi-Agent Decision Intelligence Engine for Hospital Digital Twin",
    version="0.1.0",
)

# Allow frontend (React/etc) to call this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "env": settings.env,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
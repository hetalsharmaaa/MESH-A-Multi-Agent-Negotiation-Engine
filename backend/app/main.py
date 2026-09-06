from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.database import engine, Base
from app.db import models  # noqa: F401 — needed so SQLAlchemy registers the tables

app = FastAPI(
    title="MESH - Multi-Agent Negotiation Engine",
    description="AI-Driven Multi-Agent Decision Intelligence Engine for Hospital Digital Twin",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(router)
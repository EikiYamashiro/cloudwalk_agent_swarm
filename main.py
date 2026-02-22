import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers.message_router import router as message_router
from services.store_service import init_transfer_store

app = FastAPI(title = "Cloudwalk Agent Swarm")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message_router)

@app.on_event("startup")
def startup_event() -> None:
    init_transfer_store(app)

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}

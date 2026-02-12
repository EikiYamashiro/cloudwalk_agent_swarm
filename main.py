from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from routers.message_router import router as message_router
from services.store_service import init_transfer_store

app = FastAPI(title = "Cloudwalk Agent Swarm")

app.include_router(message_router)

@app.on_event("startup")
def startup_event() -> None:
    init_transfer_store(app)

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}

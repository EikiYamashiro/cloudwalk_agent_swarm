from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel

from services.agent_service import get_answer
router = APIRouter()

class MessageRequest(BaseModel):
    message: str
    user_id: str

class MessageResponse(BaseModel):
    response: str

@router.post("/message", response_model=MessageResponse)
def message(payload: MessageRequest) -> MessageResponse:
    response_content = get_answer(payload.message, payload.user_id)
    return MessageResponse(response=response_content)

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agent_service import get_answer
from services.store_service import get_customer_by_user_id, get_or_create_customer, list_transfers

router = APIRouter()


class MessageRequest(BaseModel):
    message: str
    user_id: str


class MessageResponse(BaseModel):
    response: str


class TransferResponse(BaseModel):
    amount: float
    direction: str
    counterparty: str
    status: str
    created_at: str


class TransferListResponse(BaseModel):
    user_id: str
    transfers: list[TransferResponse]


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=80)


class LoginResponse(BaseModel):
    user_id: str
    username: str


@router.post("/message", response_model=MessageResponse)
def message(payload: MessageRequest) -> MessageResponse:
    customer = get_customer_by_user_id(payload.user_id)
    if not customer:
        raise HTTPException(status_code=404, detail="User not found.")
    response_content = get_answer(
        user_input=payload.message,
        user_id=customer["user_id"],
        username=customer["username"],
    )
    return MessageResponse(response=response_content)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=422, detail="Username cannot be empty.")
    customer = get_or_create_customer(username)
    return LoginResponse(user_id=customer["user_id"], username=customer["username"])


@router.get("/customers/{user_id}/transfers", response_model=TransferListResponse)
def get_transfers(user_id: str, limit: int = 10) -> TransferListResponse:
    if not get_customer_by_user_id(user_id):
        raise HTTPException(status_code=404, detail="User not found.")
    safe_limit = max(1, min(limit, 50))
    transfers = list_transfers(user_id=user_id, limit=safe_limit)
    transfer_items = [TransferResponse(**item) for item in transfers]
    return TransferListResponse(user_id=user_id, transfers=transfer_items)

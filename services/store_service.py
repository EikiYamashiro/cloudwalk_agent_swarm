from __future__ import annotations

from threading import Lock
from typing import Any
from fastapi import FastAPI

transfer_list: list[dict[str, Any]] = []
transfer_lock = Lock()


def init_transfer_store(app: FastAPI | None = None) -> None:
    global transfer_list
    with transfer_lock:
        transfer_list = []
    if app is not None:
        app.state.transfer_list = transfer_list
        app.state.transfer_lock = transfer_lock


def add_transfer(user_id: str, amount: float, destination: str) -> dict[str, Any]:
    transfer = {
        "user_id": user_id,
        "amount": amount,
        "destination": destination,
        "status": "success",
    }
    with transfer_lock:
        transfer_list.append(transfer)
    return transfer


def get_last_transfer(user_id: str) -> dict[str, Any] | None:
    with transfer_lock:
        user_transfers = [item for item in transfer_list if item["user_id"] == user_id]
    if not user_transfers:
        return None
    return user_transfers[-1]

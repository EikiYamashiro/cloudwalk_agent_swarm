from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

current_user_id: ContextVar[str] = ContextVar("current_user_id", default="")
current_username: ContextVar[str] = ContextVar("current_username", default="")


def get_current_user() -> tuple[str, str]:
    return current_user_id.get(), current_username.get()


@contextmanager
def user_context(user_id: str, username: str) -> Iterator[None]:
    user_id_token = current_user_id.set((user_id or "").strip())
    username_token = current_username.set((username or "").strip())
    try:
        yield
    finally:
        current_user_id.reset(user_id_token)
        current_username.reset(username_token)

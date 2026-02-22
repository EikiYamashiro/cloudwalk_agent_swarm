from __future__ import annotations

import os

MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "2000"))
MAX_TRANSFER_AMOUNT = float(os.getenv("MAX_TRANSFER_AMOUNT", "20000"))


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def validate_input_message(message: str) -> tuple[bool, str | None]:
    normalized = _normalize_text(message)
    if not normalized:
        return True, "Empty message."

    if len(normalized) > MAX_INPUT_CHARS:
        return True, f"Message too long (limit: {MAX_INPUT_CHARS} chars)."

    return False, None


def validate_transfer_payload(amount: float, destination: str) -> tuple[bool, str | None]:
    clean_destination = _normalize_text(destination)
    if not clean_destination:
        return True, "Destination is required."

    if amount <= 0:
        return True, "Transfer amount must be greater than zero."

    if amount > MAX_TRANSFER_AMOUNT:
        return True, f"Transfer amount exceeds allowed limit ({MAX_TRANSFER_AMOUNT:.2f})."

    return False, None


def sanitize_output(text: str) -> str:
    return text or ""

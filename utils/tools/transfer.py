from langchain_core.tools import tool

from services.guardrail_service import validate_transfer_payload
from services.request_context import get_current_user
from services.store_service import (
    add_transfer,
    get_last_transfer as get_last_transfer_record,
    get_transfers_from_user as get_transfers_from_user_record,
)


def _get_request_user_id() -> str:
    user_id, _ = get_current_user()
    return (user_id or "").strip()


@tool
def transfer(amount: float, counterparty_name: str) -> str:
    """Create a transfer for the current request user."""
    user_id = _get_request_user_id()
    if not user_id:
        return "Transfer rejected: missing request user context."

    blocked, reason = validate_transfer_payload(
        amount=amount,
        counterparty_name=counterparty_name,
    )
    if blocked:
        return f"Transfer rejected: {reason}"

    transfer_data = add_transfer(
        user_id=user_id,
        amount=amount,
        counterparty_name=counterparty_name,
    )
    if not transfer_data:
        return (
            "Transfer rejected: counterparty not found. "
            "Please provide the exact name or client id."
        )

    return (
        f"Transfer created for user {transfer_data['user_id']} with amount "
        f"{transfer_data['amount']} to {transfer_data['counterparty']}."
    )


@tool
def get_last_transfer() -> str:
    """Get the latest transfer for the current request user."""
    user_id = _get_request_user_id()
    if not user_id:
        return "No transfers found: missing request user context."

    transfer_data = get_last_transfer_record(user_id=user_id)
    if not transfer_data:
        return f"No transfers found for user {user_id}."
    return (
        f"Last transfer for user {user_id}: "
        f"{transfer_data['direction']} {transfer_data['amount']} with {transfer_data['counterparty']} "
        f"with status {transfer_data['status']}."
    )


@tool
def get_transfers_from_user() -> str:
    """Get all transfers for the current request user."""
    user_id = _get_request_user_id()
    if not user_id:
        return "No transfers found: missing request user context."

    transfers = get_transfers_from_user_record(user_id=user_id)
    if not transfers:
        return f"No transfers found for user {user_id}."

    lines = []
    for index, transfer_data in enumerate(transfers, start=1):
        lines.append(
            f"{index}. {transfer_data['direction']} {transfer_data['amount']:.2f} "
            f"with {transfer_data['counterparty']} | status: {transfer_data['status']} "
            f"| created_at: {transfer_data['created_at']}"
        )

    return f"Transfer history for user {user_id} ({len(transfers)} records):\n" + "\n".join(lines)

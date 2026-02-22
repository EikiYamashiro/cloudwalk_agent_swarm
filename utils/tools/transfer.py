from langchain_core.tools import tool

from services.guardrail_service import validate_transfer_payload
from services.store_service import (
    add_transfer,
    get_last_transfer as get_last_transfer_record,
    get_transfers_from_user as get_transfers_from_user_record,
)

@tool
def transfer(user_id: str, amount: float, destination: str) -> str:
    """Create a transfer for a user and store it in Postgres."""
    blocked, reason = validate_transfer_payload(amount=amount, destination=destination)
    if blocked:
        return f"Transfer rejected: {reason}"

    transfer_data = add_transfer(user_id=user_id, amount=amount, destination=destination)
    return (
        f"Transfer created for user {transfer_data['user_id']} with amount "
        f"{transfer_data['amount']} to {transfer_data['destination']}."
    )


@tool
def get_last_transfer(user_id: str) -> str:
    """Get the latest transfer for a given user_id."""
    transfer_data = get_last_transfer_record(user_id=user_id)
    if not transfer_data:
        return f"No transfers found for user {user_id}."
    return (
        f"Last transfer for user {user_id}: "
        f"{transfer_data['direction']} {transfer_data['amount']} with {transfer_data['counterparty']} "
        f"with status {transfer_data['status']}."
    )


@tool
def get_transfers_from_user(user_id: str) -> str:
    """Get all transfers for a given user_id."""
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

from langchain_core.tools import tool
from services.store_service import add_transfer, get_last_transfer as get_last_transfer_record


@tool
def transfer(user_id: str, amount: float, destination: str) -> str:
    """Create a transfer for a user and store it in memory."""
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
        f"Last transfer for user {transfer_data['user_id']}: "
        f"amount {transfer_data['amount']} to {transfer_data['destination']} "
        f"with status {transfer_data['status']}."
    )

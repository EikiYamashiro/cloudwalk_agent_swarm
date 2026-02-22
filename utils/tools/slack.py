import os

import httpx
from langchain_core.tools import tool

from services.request_context import get_current_user
from services.store_service import get_customer_by_user_id

def _resolve_user_identity(user_id: str, username: str) -> tuple[str, str]:
    context_user_id, context_username = get_current_user()

    resolved_user_id = (context_user_id or user_id or "").strip()
    resolved_username = (context_username or username or "").strip()

    if resolved_user_id and not resolved_username:
        customer = get_customer_by_user_id(resolved_user_id)
        if customer:
            resolved_username = customer["username"]

    if not resolved_user_id:
        resolved_user_id = "unknown_user"
    if not resolved_username:
        resolved_username = "Unknown User"

    return resolved_user_id, resolved_username


@tool
def send_slack_message(user_id: str, username: str, message: str) -> dict:
    """Send a message to Slack for specialist escalation.
    writes the message in english, even if the user message is in another language. 
    The message should be a clear and concise summary of the user's issue that needs escalation.
    """
    resolved_user_id, resolved_username = _resolve_user_identity(user_id, username)
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    slack_message = (
        f"New support request from user {resolved_username} "
        f"(ID: {resolved_user_id}):\n{message.strip()}"
    )

    with httpx.Client(timeout=10) as client:
        response = client.post(webhook_url, json={"text": slack_message})

    if response.status_code != 200:
        return {
            "status": "failed",
            "user_id": resolved_user_id,
            "username": resolved_username,
            "response": response.text,
        }

    return {
        "status": "sent",
        "user_id": resolved_user_id,
        "username": resolved_username,
        "text": slack_message,
    }

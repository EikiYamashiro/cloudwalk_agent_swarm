from langchain_core.tools import tool

from services.request_context import get_current_user


def get_customer_by_user_id(user_id: str):
    from services.store_service import get_customer_by_user_id as _get_customer_by_user_id

    return _get_customer_by_user_id(user_id)


def list_transfers(user_id: str, limit: int):
    from services.store_service import list_transfers as _list_transfers

    return _list_transfers(user_id=user_id, limit=limit)


def _resolve_user_id(user_id: str) -> str:
    context_user_id, _ = get_current_user()
    return (context_user_id or user_id or "").strip()


@tool
def get_customer_support_snapshot() -> str:
    """Get customer profile and recent activity for support diagnostics."""
    resolved_user_id = _resolve_user_id("")
    if not resolved_user_id:
        return "Support snapshot not found."

    customer = get_customer_by_user_id(resolved_user_id)
    if not customer:
        return f"Support snapshot not found for user {resolved_user_id}."

    transfers = list_transfers(user_id=resolved_user_id, limit=5)
    summary_lines = [
        "Customer support snapshot:",
        f"- user_id: {customer['user_id']}",
        f"- username: {customer['username']}",
        f"- recent_activity_count: {len(transfers)}",
    ]

    if not transfers:
        summary_lines.append("Recent activity: no transfers found.")
        return "\n".join(summary_lines)

    lines = ["Recent activity:"]
    for index, transfer in enumerate(transfers, start=1):
        lines.append(
            f"{index}. {transfer['direction']} {transfer['amount']:.2f} with "
            f"{transfer['counterparty']} | status: {transfer['status']}"
        )

    return "\n".join(summary_lines + lines)

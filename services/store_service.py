from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from services.db_service import get_connection, init_db


def init_transfer_store(app: FastAPI | None = None) -> None:
    init_db()
    if app is not None:
        app.state.db_ready = True


def _normalize_username(username: str) -> str:
    return " ".join(username.strip().split())


def _build_client_id(numeric_id: int) -> str:
    return f"client{numeric_id:03d}"


def _get_customer_by_username(username: str) -> dict[str, str] | None:
    normalized = _normalize_username(username)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username
                FROM customers
                WHERE lower(username) = lower(%s)
                LIMIT 1
                """,
                (normalized,),
            )
            row = cursor.fetchone()
    if not row:
        return None
    return {"user_id": str(row["user_id"]), "username": str(row["username"])}


def get_customer_by_user_id(user_id: str) -> dict[str, str] | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username
                FROM customers
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
    if not row:
        return None
    return {"user_id": str(row["user_id"]), "username": str(row["username"])}


def get_or_create_customer(username: str) -> dict[str, str]:
    normalized = _normalize_username(username)
    existing = _get_customer_by_username(normalized)
    if existing:
        return existing

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT nextval(pg_get_serial_sequence('customers', 'id')) AS next_id
                """
            )
            next_id_row = cursor.fetchone()
            next_id = int(next_id_row["next_id"])
            user_id = _build_client_id(next_id)
            cursor.execute(
                """
                INSERT INTO customers (id, user_id, username)
                VALUES (%s, %s, %s)
                RETURNING user_id, username
                """,
                (next_id, user_id, normalized),
            )
            created = cursor.fetchone()
        conn.commit()
    return {"user_id": str(created["user_id"]), "username": str(created["username"])}


def _ensure_customer_by_user_id(user_id: str) -> None:
    existing = get_customer_by_user_id(user_id)
    if existing:
        return
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT nextval(pg_get_serial_sequence('customers', 'id')) AS next_id
                """
            )
            next_id_row = cursor.fetchone()
            next_id = int(next_id_row["next_id"])
            cursor.execute(
                """
                INSERT INTO customers (id, user_id, username)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (next_id, user_id, user_id),
            )
        conn.commit()


def _resolve_customer_from_destination(destination: str) -> dict[str, str] | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username
                FROM customers
                WHERE user_id = %s OR lower(username) = lower(%s)
                LIMIT 1
                """,
                (destination, destination),
            )
            row = cursor.fetchone()
    if not row:
        return None
    return {"user_id": str(row["user_id"]), "username": str(row["username"])}


def add_transfer(user_id: str, amount: float, destination: str) -> dict[str, Any]:
    _ensure_customer_by_user_id(user_id)
    recipient = _resolve_customer_from_destination(destination)
    recipient_user_id = recipient["user_id"] if recipient else None
    counterparty = recipient["username"] if recipient else destination

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO transfers (
                    user_id,
                    from_user_id,
                    to_user_id,
                    destination,
                    counterparty,
                    amount,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'success')
                RETURNING from_user_id, to_user_id, counterparty, amount, status, created_at
                """,
                (
                    user_id,
                    user_id,
                    recipient_user_id,
                    destination,
                    counterparty,
                    amount,
                ),
            )
            transfer = cursor.fetchone()
        conn.commit()

    return {
        "user_id": str(transfer["from_user_id"]),
        "amount": float(transfer["amount"]),
        "destination": str(transfer["counterparty"]),
        "status": str(transfer["status"]),
        "direction": "sent",
        "counterparty": str(transfer["counterparty"]),
        "created_at": transfer["created_at"].isoformat(),
    }


def _map_transfer_row(row: dict[str, Any], user_id: str) -> dict[str, Any]:
    from_user_id = str(row["from_user_id"])
    direction = "sent" if from_user_id == user_id else "received"

    if direction == "sent":
        counterparty = row["receiver_username"] or row["counterparty"] or row["to_user_id"]
    else:
        counterparty = row["sender_username"] or row["from_user_id"]
    if not counterparty:
        counterparty = "Unknown"

    return {
        "amount": float(row["amount"]),
        "status": str(row["status"]),
        "direction": direction,
        "counterparty": str(counterparty),
        "created_at": row["created_at"].isoformat(),
    }


def get_last_transfer(user_id: str) -> dict[str, Any] | None:
    if not get_customer_by_user_id(user_id):
        return None
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.from_user_id,
                    t.to_user_id,
                    t.counterparty,
                    t.amount,
                    t.status,
                    t.created_at,
                    sender.username AS sender_username,
                    receiver.username AS receiver_username
                FROM transfers t
                LEFT JOIN customers sender ON sender.user_id = t.from_user_id
                LEFT JOIN customers receiver ON receiver.user_id = t.to_user_id
                WHERE t.from_user_id = %s OR t.to_user_id = %s
                ORDER BY t.created_at DESC
                LIMIT 1
                """,
                (user_id, user_id),
            )
            row = cursor.fetchone()
    if not row:
        return None
    return _map_transfer_row(row, user_id)


def list_transfers(user_id: str, limit: int = 10) -> list[dict[str, Any]]:
    if not get_customer_by_user_id(user_id):
        return []
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.from_user_id,
                    t.to_user_id,
                    t.counterparty,
                    t.amount,
                    t.status,
                    t.created_at,
                    sender.username AS sender_username,
                    receiver.username AS receiver_username
                FROM transfers t
                LEFT JOIN customers sender ON sender.user_id = t.from_user_id
                LEFT JOIN customers receiver ON receiver.user_id = t.to_user_id
                WHERE t.from_user_id = %s OR t.to_user_id = %s
                ORDER BY t.created_at DESC
                LIMIT %s
                """,
                (user_id, user_id, limit),
            )
            rows = cursor.fetchall()

    return [_map_transfer_row(row, user_id) for row in rows]


def get_transfers_from_user(user_id: str) -> list[dict[str, Any]]:
    if not get_customer_by_user_id(user_id):
        return []
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.from_user_id,
                    t.to_user_id,
                    t.counterparty,
                    t.amount,
                    t.status,
                    t.created_at,
                    sender.username AS sender_username,
                    receiver.username AS receiver_username
                FROM transfers t
                LEFT JOIN customers sender ON sender.user_id = t.from_user_id
                LEFT JOIN customers receiver ON receiver.user_id = t.to_user_id
                WHERE t.from_user_id = %s OR t.to_user_id = %s
                ORDER BY t.created_at DESC
                """,
                (user_id, user_id),
            )
            rows = cursor.fetchall()

    return [_map_transfer_row(row, user_id) for row in rows]

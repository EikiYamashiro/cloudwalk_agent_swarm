from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/cloudwalk"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip()


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
        yield conn


def _normalize_counterparty_name(name: str) -> str:
    return " ".join((name or "").strip().split())


def find_customer_by_counterparty_name(counterparty_name: str) -> dict[str, str] | None:
    normalized = _normalize_counterparty_name(counterparty_name)
    if not normalized:
        return None

    tokens = [token for token in normalized.lower().split(" ") if token]
    unique_tokens: list[str] = []
    for token in tokens:
        if token not in unique_tokens:
            unique_tokens.append(token)

    where_parts = [
        "lower(user_id) = lower(%s)",
        "lower(username) = lower(%s)",
        "lower(username) LIKE %s",
    ]
    params: list[str] = [normalized, normalized, f"%{normalized.lower()}%"]

    for token in unique_tokens:
        where_parts.append("lower(username) LIKE %s")
        params.append(f"%{token}%")

    where_sql = " OR ".join(where_parts)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT user_id, username
                FROM customers
                WHERE {where_sql}
                ORDER BY
                    CASE
                        WHEN lower(username) = lower(%s) THEN 0
                        WHEN lower(user_id) = lower(%s) THEN 1
                        WHEN lower(username) LIKE %s THEN 2
                        ELSE 3
                    END,
                    length(username) ASC
                LIMIT 1
                """,
                (
                    *params,
                    normalized,
                    normalized,
                    f"%{normalized.lower()}%",
                ),
            )
            row = cursor.fetchone()

    if not row:
        return None
    return {"user_id": str(row["user_id"]), "username": str(row["username"])}


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                ALTER TABLE customers
                ADD COLUMN IF NOT EXISTS username TEXT
                """
            )
            cursor.execute(
                """
                UPDATE customers
                SET username = user_id
                WHERE username IS NULL OR username = ''
                """
            )
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS customers_username_lower_idx
                ON customers ((lower(username)))
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transfers (
                    id SERIAL PRIMARY KEY,
                    from_user_id TEXT,
                    to_user_id TEXT,
                    counterparty TEXT,
                    amount NUMERIC(14, 2) NOT NULL,
                    status TEXT NOT NULL DEFAULT 'success',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                ALTER TABLE transfers
                ADD COLUMN IF NOT EXISTS from_user_id TEXT
                """
            )
            cursor.execute(
                """
                ALTER TABLE transfers
                ADD COLUMN IF NOT EXISTS to_user_id TEXT
                """
            )
            cursor.execute(
                """
                ALTER TABLE transfers
                ADD COLUMN IF NOT EXISTS counterparty TEXT
                """
            )
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'transfers' AND column_name = 'user_id'
                    ) THEN
                        EXECUTE '
                            UPDATE transfers
                            SET from_user_id = user_id
                            WHERE from_user_id IS NULL AND user_id IS NOT NULL
                        ';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'transfers' AND column_name = 'destination'
                    ) THEN
                        EXECUTE '
                            UPDATE transfers
                            SET counterparty = destination
                            WHERE counterparty IS NULL AND destination IS NOT NULL
                        ';
                    END IF;
                END $$;
                """
            )
            cursor.execute(
                """
                ALTER TABLE transfers
                DROP COLUMN IF EXISTS user_id
                """
            )
            cursor.execute(
                """
                ALTER TABLE transfers
                DROP COLUMN IF EXISTS destination
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS transfers_from_user_idx
                ON transfers (from_user_id, created_at DESC)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS transfers_to_user_idx
                ON transfers (to_user_id, created_at DESC)
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS guardrail_events (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    user_message TEXT,
                    safety_decision TEXT,
                    safety_category TEXT,
                    blocked_reason TEXT,
                    blocked_at_node TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS guardrail_events_user_idx
                ON guardrail_events (user_id, created_at DESC)
                """
            )
        conn.commit()

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
                    user_id TEXT,
                    from_user_id TEXT,
                    to_user_id TEXT,
                    destination TEXT,
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
                ADD COLUMN IF NOT EXISTS user_id TEXT
                """
            )
            cursor.execute(
                """
                ALTER TABLE transfers
                ADD COLUMN IF NOT EXISTS destination TEXT
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
                UPDATE transfers
                SET from_user_id = user_id
                WHERE from_user_id IS NULL AND user_id IS NOT NULL
                """
            )
            cursor.execute(
                """
                UPDATE transfers
                SET counterparty = destination
                WHERE counterparty IS NULL AND destination IS NOT NULL
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
        conn.commit()

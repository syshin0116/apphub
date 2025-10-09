"""Database connection management."""

import os
from typing import Optional

import asyncpg
from asyncpg import Pool

_pool: Optional[Pool] = None


async def get_db_pool() -> Pool:
    """Get or create the database connection pool."""
    global _pool

    if _pool is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://apphub:apphub_dev_password@localhost:5432/apphub",
        )

        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )

        # Register vector type
        async def _setup(conn):
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.set_type_codec(
                "vector",
                encoder=lambda v: str(list(v)),
                decoder=lambda s: [float(x) for x in s[1:-1].split(",")],
                schema="public",
                format="text",
            )

        # Run setup on a connection
        async with _pool.acquire() as conn:
            await _setup(conn)

    return _pool


async def close_db_pool():
    """Close the database connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None

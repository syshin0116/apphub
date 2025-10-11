#!/usr/bin/env python3
"""Initialize LangGraph checkpoint tables in PostgreSQL.

This script should be run once before starting the LangGraph server
to create the necessary checkpoint tables.

Usage:
    uv run python scripts/init_checkpointer.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def init_checkpointer():
    """Initialize checkpoint tables."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool
    import psycopg

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://apphub:apphub_dev_password@localhost:5432/apphub",
    )

    print("🔧 Initializing LangGraph checkpoint tables...")
    print(
        f"📍 Database: {database_url.split('@')[1] if '@' in database_url else database_url}"
    )
    print()

    # Create connection pool with required configuration
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": psycopg.rows.dict_row,
    }

    pool = AsyncConnectionPool(
        conninfo=database_url,
        kwargs=connection_kwargs,
        min_size=1,
        max_size=5,
    )

    try:
        async with pool:
            checkpointer = AsyncPostgresSaver(pool)
            print("1️⃣  Running migrations...")
            await checkpointer.setup()
            print("   ✅ Migrations completed")
            print()

            # Verify tables were created using a connection from the pool
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name LIKE 'checkpoint%'
                        ORDER BY table_name
                    """
                    )
                    tables = await cur.fetchall()

                    print("2️⃣  Verifying tables...")
                    print(f"   ✅ Created {len(tables)} tables:")
                    for table in tables:
                        await cur.execute(f"SELECT COUNT(*) FROM {table['table_name']}")
                        count_result = await cur.fetchone()
                        count = count_result["count"] if count_result else 0
                        print(f"      - {table['table_name']} ({count} rows)")
            print()
            print("=" * 60)
            print("✅ Checkpoint tables initialized successfully!")
            print("=" * 60)
            print()
            print("You can now start the LangGraph server:")
            print("  cd apps/ai-service")
            print("  uv run langgraph dev")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_checkpointer())

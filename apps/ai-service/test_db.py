"""Test database connection."""

import asyncio

from src.db import get_db_pool, close_db_pool


async def main():
    print("🔌 Connecting to database...")
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # Test basic query
        version = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL version: {version[:50]}...")

        # Test pgvector extension
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
        )
        if result:
            print("✅ pgvector extension installed")
        else:
            print("❌ pgvector extension not found")

        # Test tables
        tables = await conn.fetch(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        print(f"✅ Found tables: {[t['tablename'] for t in tables]}")

    await close_db_pool()
    print("✨ Database connection test completed!")


if __name__ == "__main__":
    asyncio.run(main())

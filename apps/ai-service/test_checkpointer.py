"""Test script to verify AsyncPostgresSaver checkpoint setup."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_checkpointer_setup():
    """Test that checkpoint tables are created properly."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    import asyncpg

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://apphub:apphub_dev_password@localhost:5432/apphub",
    )

    print(f"📍 Testing connection to: {database_url}")
    print()

    # Initialize checkpointer using async context manager
    print("1️⃣  Initializing AsyncPostgresSaver...")
    async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
        print("   ✅ Checkpointer initialized")
        print()

        # Setup tables
        print("2️⃣  Running checkpointer.setup()...")
        try:
            await checkpointer.setup()
            print("   ✅ Setup completed successfully")
        except Exception as e:
            print(f"   ❌ Setup failed: {e}")
            return
        print()

        # Verify tables exist
        print("3️⃣  Verifying checkpoint tables...")
        try:
            conn = await asyncpg.connect(database_url)

            # Get list of checkpoint-related tables
            tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'checkpoint%'
                ORDER BY table_name
            """)

            print(f"   Found {len(tables)} checkpoint tables:")
            for table in tables:
                table_name = table['table_name']

                # Get row count
                count_result = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")

                # Get column info
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)

                print(f"\n   📊 {table_name} ({count_result} rows)")
                for col in columns:
                    print(f"      - {col['column_name']}: {col['data_type']}")

            await conn.close()
            print("\n   ✅ All tables verified")
        except Exception as e:
            print(f"   ❌ Verification failed: {e}")
            return
        print()

        print("4️⃣  Testing checkpoint save/load...")
        try:
            # Test basic checkpoint operations
            from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
            from uuid import uuid4

            thread_id = str(uuid4())
            checkpoint_id = str(uuid4())

            # Create a simple checkpoint
            checkpoint = Checkpoint(
                v=1,
                id=checkpoint_id,
                ts="2024-01-01T00:00:00",
                channel_values={},
                channel_versions={},
                versions_seen={},
                pending_sends=[],
            )

            metadata = CheckpointMetadata(
                source="input",
                step=0,
                writes={},
                parents={},
            )

            # Save checkpoint
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": "",
                    "checkpoint_id": checkpoint_id,
                }
            }

            await checkpointer.aput(
                config,
                checkpoint,
                metadata,
                {},
            )
            print(f"   ✅ Saved checkpoint: {checkpoint_id}")

            # Load checkpoint
            loaded = await checkpointer.aget(config)
            if loaded:
                print(f"   ✅ Loaded checkpoint: {loaded.checkpoint.id}")
            else:
                print(f"   ❌ Could not load checkpoint")

        except Exception as e:
            print(f"   ⚠️  Checkpoint test warning: {e}")
            import traceback
            traceback.print_exc()
        print()

        print("=" * 60)
        print("✅ Checkpointer setup test completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_checkpointer_setup())

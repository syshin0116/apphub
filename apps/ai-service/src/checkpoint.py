"""PostgreSQL checkpoint configuration for LangGraph."""

import os

from langgraph.checkpoint.postgres import PostgresSaver


def get_checkpointer():
    """Get PostgreSQL checkpointer for LangGraph state persistence."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://apphub:apphub_dev_password@localhost:5432/apphub",
    )

    # Create checkpointer with connection string
    checkpointer = PostgresSaver.from_conn_string(database_url)

    return checkpointer

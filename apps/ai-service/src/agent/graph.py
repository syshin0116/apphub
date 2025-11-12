"""LangGraph ReAct agent with AsyncPostgreSQL checkpoint."""

from __future__ import annotations

import os
from typing import Annotated, Literal
from pydantic import Field

from langchain.agents import create_agent
from typing_extensions import TypedDict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import psycopg

# Import agent-tools
from agent_tools import SessionSandbox, create_atomic_tools


class ContextSchema(TypedDict):
    """Context parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    model: Annotated[
        Literal[
            "openai:gpt-4.1",
            "openai:gpt-4.1-mini",
            "openai:gpt-4.1-nano",
            {"__template__metadata__": {"kind": "llm"}},
        ],
        Field(
            default="openai:gpt-4.1",
            description="The model to use for the agent. Available models: openai:gpt-4.1, openai:gpt-4.1-mini, openai:gpt-4.1-nano",
        ),
        "Should be in format of <provider>/<model>",
    ]


# Helper function to create user agent with sandboxed tools
def create_user_agent(user_id: str, session_id: str, checkpointer_factory):
    """
    Create user-specific agent with sandboxed tools

    Args:
        user_id: User ID
        session_id: Session ID (thread_id)
        checkpointer_factory: Checkpointer factory function

    Returns:
        Compiled LangGraph agent
    """
    # Create session sandbox (isolated workspace)
    sandbox = SessionSandbox(user_id=user_id, session_id=session_id)

    # Create atomic tools (4 only!)
    tools = create_atomic_tools(sandbox)

    # Create agent
    agent = create_agent(
        model="openai:gpt-4.1",
        tools=tools,
        checkpointer=checkpointer_factory,
        name=f"Agent-{user_id}",
        system_prompt=(
            f"You are a helpful AI assistant for user {user_id}.\n\n"
            "You have access to 4 atomic tools:\n"
            "1. file_read(path) - Read files\n"
            "2. file_write(path, content) - Write files\n"
            "3. file_list(directory, pattern) - List files with glob patterns\n"
            "4. shell_execute(command) - Execute shell commands (gateway to advanced features)\n\n"
            f"Your working directory: {sandbox.sandbox_dir}\n"
            "All file operations are restricted to this directory for security.\n\n"
            "For complex tasks, use shell_execute to call Linux commands:\n"
            "- grep, find, awk: Text processing\n"
            "- python scripts: Data analysis\n"
            "- Future: knowledge-search (semantic search), mcp-cli (MCP tools)\n\n"
            "Think step by step and explain your reasoning.\n"
        ),
    )

    return agent, sandbox


# Database connection string for checkpointer
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://apphub:apphub_dev_password@localhost:5432/apphub",
)


def make_checkpointer():
    """Create AsyncPostgresSaver with connection pool.

    This factory function is called by LangGraph in an async context,
    ensuring the event loop is available for pool initialization.
    """
    # Connection pool configuration:
    # - autocommit=True: Required for setup() to properly commit checkpoint tables
    # - prepare_threshold=0: Prevents "prepared statement already exists" errors
    # - row_factory=dict_row: Required by PostgresSaver implementation
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": psycopg.rows.dict_row,
    }

    # Create async connection pool
    # This is called within an async context by LangGraph, so event loop is available
    pool = AsyncConnectionPool(
        conninfo=database_url,
        kwargs=connection_kwargs,
        min_size=1,
        max_size=10,
    )

    # Initialize AsyncPostgresSaver with connection pool
    # NOTE: setup() should be run once via scripts/init_checkpointer.py before first use
    return AsyncPostgresSaver(pool)

# Legacy: Create default agent (backward compatibility)
# For production, use create_user_agent() instead
def _create_default_graph():
    """Create default agent for backward compatibility"""
    sandbox = SessionSandbox(user_id="default", session_id="default")
    tools = create_atomic_tools(sandbox)

    return create_agent(
        model="openai:gpt-4.1",
        tools=tools,
        checkpointer=make_checkpointer,
        name="AppHub Agent",
        system_prompt=(
            "You are a helpful AI assistant with access to file operations and shell commands.\n"
            "Think step by step and explain your reasoning."
        ),
    )

# Default graph instance
graph = _create_default_graph()

"""LangGraph ReAct agent with AsyncPostgreSQL checkpoint."""

from __future__ import annotations

import os
from typing import Annotated, Literal
from pydantic import Field

from langchain.agents import create_agent
from langchain_core.tools import tool
from typing_extensions import TypedDict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import psycopg


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


# Define example tools for the ReAct agent
@tool
def search_tool(query: str) -> str:
    """Search for information on the web.

    Args:
        query: The search query string

    Returns:
        Search results as a string
    """
    # Placeholder implementation
    return f"Search results for: {query}"


@tool
def calculator_tool(expression: str) -> str:
    """Perform mathematical calculations.

    Args:
        expression: A mathematical expression to evaluate

    Returns:
        The calculation result
    """
    try:
        # Safe eval for basic math operations
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


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

# Create ReAct agent with AsyncPostgresSaver checkpointer factory
graph = create_agent(
    model="openai:gpt-4.1",
    tools=[search_tool, calculator_tool],
    checkpointer=make_checkpointer,  # Pass factory function, not instance
    name="AppHub ReAct Agent",
    system_prompt=(
        "You are a helpful AI assistant with access to tools. "
        "Use the search tool to find information and the calculator tool for math operations. "
        "Think step by step and explain your reasoning."
    ),
)

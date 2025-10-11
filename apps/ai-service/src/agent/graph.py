"""LangGraph ReAct agent with AsyncPostgreSQL checkpoint."""

from __future__ import annotations

import os
from typing import Annotated, Literal
from pydantic import Field

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.agents import create_agent
from langchain_core.tools import tool
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model


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


# Initialize AsyncPostgresSaver with database connection
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://apphub:apphub_dev_password@localhost:5432/apphub",
)
checkpointer = AsyncPostgresSaver.from_conn_string(database_url)

# Initialize the language model
model = init_chat_model(
    model=os.getenv("DEFAULT_MODEL", "openai:gpt-4.1"),
    temperature=0,
)

# Define available tools
tools = [search_tool, calculator_tool]

# Create ReAct agent with AsyncPostgresSaver checkpointer
graph = create_agent(
    model="openai:gpt-4.1",
    tools=tools,
    checkpointer=checkpointer,
    name="AppHub ReAct Agent",
    system_prompt=(
        "You are a helpful AI assistant with access to tools. "
        "Use the search tool to find information and the calculator tool for math operations. "
        "Think step by step and explain your reasoning."
    ),
)

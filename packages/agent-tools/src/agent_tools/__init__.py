"""
Agent Tools: Domain-Agnostic Tool Architecture for AI Agents

3-tier architecture following Manus pattern:
- Level 1: Atomic Functions (4 tools) - Python @tool
- Level 2: CLI Utilities (unlimited) - Python package → CLI
- Level 3: Domain Implementations (unlimited) - Python scripts

Usage:
    >>> from agent_tools.sandbox import SessionSandbox
    >>> from agent_tools.level1 import create_atomic_tools
    >>>
    >>> # Create session sandbox
    >>> sandbox = SessionSandbox(user_id="alice", session_id="abc123")
    >>>
    >>> # Create tools
    >>> tools = create_atomic_tools(sandbox)
    >>>
    >>> # Use in LangGraph
    >>> from langchain.agents import create_agent
    >>> graph = create_agent(model="openai:gpt-4", tools=tools)
"""

__version__ = "0.1.0"

from .sandbox import SessionSandbox
from .level1 import create_atomic_tools

__all__ = ["SessionSandbox", "create_atomic_tools"]

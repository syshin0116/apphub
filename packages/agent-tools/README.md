# AppHub Agent Tools

Domain-agnostic Agent Tools with 3-tier architecture following Manus pattern.

## Architecture

```
Level 1: Atomic Functions (4 tools)
  ├─ file_read       - Read files
  ├─ file_write      - Write files
  ├─ file_list       - List files (glob)
  └─ shell_execute   - Execute shell commands (gateway to Level 2/3)

Level 2: CLI Utilities (unlimited, future)
  ├─ knowledge-search - Semantic search
  └─ mcp-cli         - MCP integration

Level 3: Domain Implementations (unlimited, future)
  └─ blog/           - Blog-specific tools
```

## Installation

```bash
cd packages/agent-tools
pip install -e .
```

## Usage

```python
from agent_tools import SessionSandbox, create_atomic_tools

# Create session sandbox (isolated workspace)
sandbox = SessionSandbox(user_id="alice", session_id="abc123")

# Create tools (4 atomic functions)
tools = create_atomic_tools(sandbox)

# Use in LangGraph
from langchain.agents import create_agent

graph = create_agent(
    model="openai:gpt-4",
    tools=tools,  # 4 tools only!
)
```

## Key Features

- ✅ **Session Isolation**: Each user has isolated workspace
- ✅ **Security**: Path traversal protection
- ✅ **Context Offloading**: Large outputs saved to files
- ✅ **Type Safety**: Full Python type hints
- ✅ **KV Cache Friendly**: Only 4 tools in function space

## Testing

```bash
pytest
```

## Development

```bash
pip install -e ".[dev]"
```

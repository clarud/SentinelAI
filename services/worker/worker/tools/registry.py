import os

def _env(key: str, default: str) -> str:
    return os.getenv(key, default)

MCP_SERVERS = {
    "rag-tools": {
        "url": _env("MCP_RAG_TOOLS_URL", "ws://localhost:7031"),
        "timeout": float(_env("MCP_RAG_TOOLS_TIMEOUT_S", "3.0")),
    },
    "gmail-tools": {
        "url": _env("MCP_GMAIL_TOOLS_URL", "ws://localhost:7032"),
        "timeout": float(_env("MCP_GMAIL_TOOLS_TIMEOUT_S", "3.0")),
    },
}

# Add on other mcp servers: extraction-tools
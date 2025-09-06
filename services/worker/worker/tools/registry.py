import os

def _env(key: str, default: str) -> str:
    return os.getenv(key, default)

# Centralized MCP server configuration
CENTRALIZED_MCP_SERVER = {
    "url": _env("MCP_CENTRALIZED_URL", "ws://localhost:7030"),
    "timeout": float(_env("MCP_CENTRALIZED_TIMEOUT_S", "5.0")),
}

# All tool servers now point to the centralized server
MCP_SERVERS = {
    "rag-tools": CENTRALIZED_MCP_SERVER,
    "data-processor": CENTRALIZED_MCP_SERVER,
    "extraction-tools": CENTRALIZED_MCP_SERVER,
    "gmail-tools": CENTRALIZED_MCP_SERVER,
}
"""MCP server configurations for ALPHY."""

import os
from pathlib import Path
from typing import TypedDict, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class MCPServerConfig(TypedDict, total=False):
    """Configuration for an MCP server."""
    command: str
    args: list[str]
    cwd: Optional[str]
    env: dict[str, str]


# MCP Server Definitions
MCP_SERVERS: dict[str, MCPServerConfig] = {
    "app_store": {
        "command": "node",
        "args": ["server.js"],
        "cwd": str(PROJECT_ROOT / "mcp-servers" / "mcp-appstore"),
        "env": {},
    },
    "product_hunt": {
        "command": str(PROJECT_ROOT / ".venv" / "bin" / "product-hunt-mcp"),
        "args": [],
        "cwd": str(PROJECT_ROOT),
        "env": {
            "PRODUCT_HUNT_TOKEN": os.getenv("PRODUCT_HUNT_TOKEN", ""),
        },
    },
}


def get_server_config(server_name: str) -> MCPServerConfig:
    """Get configuration for a specific MCP server."""
    if server_name not in MCP_SERVERS:
        raise ValueError(f"Unknown MCP server: {server_name}. Available: {list(MCP_SERVERS.keys())}")
    return MCP_SERVERS[server_name]


def get_available_servers() -> list[str]:
    """Get list of available MCP server names."""
    return list(MCP_SERVERS.keys())

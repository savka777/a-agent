"""MCP client for connecting to MCP servers."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .config import get_server_config, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to and calling MCP servers."""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._contexts: dict[str, Any] = {}

    async def connect(self, server_name: str) -> ClientSession:
        """
        Connect to an MCP server by name.

        Args:
            server_name: Name of the server (e.g., "app_store", "product_hunt")

        Returns:
            ClientSession for making tool calls
        """
        if server_name in self._sessions:
            return self._sessions[server_name]

        config = get_server_config(server_name)

        server_params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            cwd=config.get("cwd"),
            env=config.get("env"),
        )

        # Create stdio connection (store context for cleanup)
        stdio_ctx = stdio_client(server_params)
        read_stream, write_stream = await stdio_ctx.__aenter__()
        self._contexts[f"{server_name}_stdio"] = stdio_ctx

        # Create session (don't use async with - we manage lifecycle manually)
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        await session.initialize()

        self._sessions[server_name] = session
        self._contexts[f"{server_name}_session"] = session
        logger.info(f"Connected to MCP server: {server_name}")
        return session

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None
    ) -> Any:
        """
        Call a tool on an MCP server.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        session = await self.connect(server_name)

        result = await session.call_tool(tool_name, arguments or {})

        # Extract content from result
        if hasattr(result, 'content') and result.content:
            # MCP returns content as a list of content blocks
            if len(result.content) == 1:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return content.text
            return [c.text if hasattr(c, 'text') else c for c in result.content]

        return result

    async def list_tools(self, server_name: str) -> list[dict[str, Any]]:
        """
        List available tools on an MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            List of tool definitions
        """
        session = await self.connect(server_name)
        result = await session.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
            }
            for tool in result.tools
        ]

    async def disconnect(self, server_name: str | None = None):
        """
        Disconnect from MCP server(s).

        Args:
            server_name: Specific server to disconnect, or None for all
        """
        if server_name:
            await self._cleanup_server(server_name)
        else:
            for name in list(self._sessions.keys()):
                await self._cleanup_server(name)
            logger.info("Disconnected from all MCP servers")

    async def _cleanup_server(self, server_name: str):
        """Clean up a single server connection."""
        # Clean up session
        session_key = f"{server_name}_session"
        if session_key in self._contexts:
            try:
                await self._contexts[session_key].__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing session for {server_name}: {e}")
            del self._contexts[session_key]

        # Clean up stdio connection
        stdio_key = f"{server_name}_stdio"
        if stdio_key in self._contexts:
            try:
                await self._contexts[stdio_key].__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing stdio for {server_name}: {e}")
            del self._contexts[stdio_key]

        # Remove session reference
        if server_name in self._sessions:
            del self._sessions[server_name]
            logger.info(f"Disconnected from MCP server: {server_name}")

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        await self.disconnect(None)


@asynccontextmanager
async def mcp_client() -> AsyncGenerator[MCPClient, None]:
    """
    Context manager for MCP client.

    Usage:
        async with mcp_client() as client:
            result = await client.call_tool("app_store", "search_app", {"term": "habit tracker"})
    """
    client = MCPClient()
    try:
        yield client
    finally:
        await client.disconnect_all()


# Singleton instance for simple usage
_client: MCPClient | None = None


async def get_client() -> MCPClient:
    """Get or create singleton MCP client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client


async def call_tool(server_name: str, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
    """
    Convenience function to call a tool.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        Tool result
    """
    client = await get_client()
    return await client.call_tool(server_name, tool_name, arguments)

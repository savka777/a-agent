"""
Test script for Revenue MCP (Smithery hosted)
Discovers available tools and tests key functionality
"""

import asyncio
import json
import httpx

# Smithery MCP endpoint
MCP_URL = "https://server.smithery.ai/@kemalersin/app-revenue-mcp/mcp"


async def discover_tools():
    """Connect to the MCP and list available tools"""
    print("🔬 Revenue MCP Discovery")
    print("=" * 50)
    print(f"\nEndpoint: {MCP_URL}\n")

    # MCP uses JSON-RPC 2.0 protocol
    # First, let's try to list tools

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try to initialize and list tools
        try:
            # MCP initialize request
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "alphy-test",
                        "version": "1.0.0"
                    }
                }
            }

            print("📡 Sending initialize request...")
            response = await client.post(
                MCP_URL,
                json=init_payload,
                headers={"Content-Type": "application/json"}
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)[:500]}")

                # Now list tools
                list_tools_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                print("\n📋 Listing tools...")
                tools_response = await client.post(
                    MCP_URL,
                    json=list_tools_payload,
                    headers={"Content-Type": "application/json"}
                )

                if tools_response.status_code == 200:
                    tools_data = tools_response.json()
                    print(f"\nTools Response:\n{json.dumps(tools_data, indent=2)}")
                else:
                    print(f"Tools request failed: {tools_response.status_code}")
                    print(tools_response.text[:500])

            else:
                print(f"Response body: {response.text[:500]}")

        except Exception as e:
            print(f"Error: {e}")

        # Try SSE endpoint (some MCPs use Server-Sent Events)
        print("\n" + "=" * 50)
        print("Trying alternative endpoints...")

        # Try the base URL
        try:
            info_response = await client.get(
                "https://smithery.ai/server/@kemalersin/app-revenue-mcp",
                headers={"Accept": "application/json"},
                follow_redirects=True
            )
            print(f"\nSmithery page status: {info_response.status_code}")
        except Exception as e:
            print(f"Error fetching info: {e}")


if __name__ == "__main__":
    asyncio.run(discover_tools())

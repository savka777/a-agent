"""
Test script for Product Hunt MCP
Tests the key tools ALPHY needs for discovering trending products
Uses MCP client to communicate with the server
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check token
token = os.getenv("PRODUCT_HUNT_TOKEN")
if not token:
    print("❌ PRODUCT_HUNT_TOKEN not found in environment")
    exit(1)

print("✅ PRODUCT_HUNT_TOKEN found\n")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_product_hunt_mcp():
    print("🔬 ALPHY Use Case Tests for Product Hunt MCP")
    print("=" * 50)

    # Get the path to the product-hunt-mcp executable
    venv_bin = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv", "bin")
    mcp_path = os.path.join(venv_bin, "product-hunt-mcp")

    server_params = StdioServerParameters(
        command=mcp_path,
        args=[],
        env={**os.environ, "PRODUCT_HUNT_TOKEN": token}
    )

    results = {}

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            print("\n📋 Available Tools:")
            print("─" * 40)
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  • {tool.name}")
            print()

            # Test 1: Check server status
            print("\n📡 TEST 1: Server Status")
            print("─" * 40)
            try:
                result = await session.call_tool("check_server_status", {})
                content = result.content[0].text if result.content else "No content"
                data = json.loads(content)
                print(f"  Status: {data.get('status', 'unknown')}")
                print(f"  Authenticated: {data.get('authenticated', False)}")
                if data.get('rate_limits'):
                    limits = data['rate_limits']
                    print(f"  Rate Limits: {limits.get('remaining', '?')}/{limits.get('limit', '?')}")
                results["Server Status"] = data.get('authenticated', False)
            except Exception as e:
                print(f"  Error: {e}")
                results["Server Status"] = False

            # Test 2: Get featured posts (key for discovering trending products)
            print("\n📱 TEST 2: Get Featured Posts")
            print("─" * 40)
            try:
                result = await session.call_tool("get_posts", {
                    "featured": True,
                    "count": 5,
                    "order": "VOTES"
                })
                content = result.content[0].text if result.content else "{}"
                data = json.loads(content)

                # Handle nested response: {"success": true, "data": {"posts": [...]}}
                posts_data = data.get("data", data)
                if posts_data.get("posts"):
                    posts = [p.get("node", p) for p in posts_data["posts"]]
                    print(f"  Found {len(posts)} featured posts:\n")
                    for post in posts[:5]:
                        print(f"  • {post.get('name', 'Unknown')}")
                        tagline = post.get('tagline', 'N/A') or 'N/A'
                        print(f"    {tagline[:60]}")
                        print(f"    Votes: {post.get('votesCount', 0)}")
                        print()
                    results["Get Featured Posts"] = True
                else:
                    print(f"  No posts in response")
                    results["Get Featured Posts"] = False
            except Exception as e:
                print(f"  Error: {e}")
                results["Get Featured Posts"] = False

            # Test 3: Get posts by topic (ALPHY's main use case)
            print("\n🏷️ TEST 3: Get Posts by Topic (AI)")
            print("─" * 40)
            try:
                result = await session.call_tool("get_posts", {
                    "topic": "artificial-intelligence",
                    "count": 5
                })
                content = result.content[0].text if result.content else "{}"
                data = json.loads(content)

                posts_data = data.get("data", data)
                if posts_data.get("posts"):
                    posts = [p.get("node", p) for p in posts_data["posts"]]
                    print(f"  Found {len(posts)} AI-related posts:\n")
                    for post in posts[:5]:
                        print(f"  • {post.get('name', 'Unknown')}")
                        tagline = post.get('tagline', 'N/A') or 'N/A'
                        print(f"    {tagline[:50]}..." if len(tagline) > 50 else f"    {tagline}")
                        print(f"    Votes: {post.get('votesCount', 0)}")
                        # Check for makers (indie indicator)
                        makers = post.get('makers', [])
                        if makers:
                            maker_names = [m.get('name', '?') for m in makers[:2]]
                            print(f"    Makers: {', '.join(maker_names)}")
                        print()
                    results["Get Posts by Topic"] = True
                else:
                    print(f"  No posts found")
                    results["Get Posts by Topic"] = False
            except Exception as e:
                print(f"  Error: {e}")
                results["Get Posts by Topic"] = False

            # Test 4: Search topics
            print("\n🔍 TEST 4: Search Topics")
            print("─" * 40)
            try:
                result = await session.call_tool("search_topics", {
                    "query": "productivity",
                    "count": 5
                })
                content = result.content[0].text if result.content else "{}"
                data = json.loads(content)

                topics_data = data.get("data", data)
                if topics_data.get("topics"):
                    topics = [t.get("node", t) for t in topics_data["topics"]]
                    print(f"  Found {len(topics)} topics matching 'productivity':\n")
                    for topic in topics[:5]:
                        print(f"  • {topic.get('name', 'Unknown')} (slug: {topic.get('slug', 'N/A')})")
                        print(f"    Followers: {topic.get('followersCount', 0)}")
                    results["Search Topics"] = True
                else:
                    print(f"  No topics found")
                    results["Search Topics"] = False
            except Exception as e:
                print(f"  Error: {e}")
                results["Search Topics"] = False

            # Test 5: Get post details (for deep research)
            print("\n📋 TEST 5: Get Post Details")
            print("─" * 40)
            try:
                # First get a post slug
                posts_result = await session.call_tool("get_posts", {"featured": True, "count": 1})
                posts_raw = json.loads(posts_result.content[0].text)
                posts_data = posts_raw.get("data", posts_raw)

                if posts_data.get("posts"):
                    first_post = posts_data["posts"][0]
                    post_node = first_post.get("node", first_post)
                    slug = post_node.get("slug")
                    print(f"  Looking up: {slug}\n")

                    result = await session.call_tool("get_post_details", {
                        "slug": slug,
                        "comments_count": 3
                    })
                    content = result.content[0].text if result.content else "{}"
                    data = json.loads(content)
                    post_data = data.get("data", data)

                    if post_data.get("post"):
                        post = post_data["post"]
                        print(f"  Name: {post.get('name', 'Unknown')}")
                        print(f"  Tagline: {post.get('tagline', 'N/A')}")
                        desc = post.get('description', 'N/A') or 'N/A'
                        print(f"  Description: {desc[:100]}...")
                        print(f"  Votes: {post.get('votesCount', 0)}")
                        print(f"  Comments: {post.get('commentsCount', 0)}")
                        print(f"  Website: {post.get('website', 'N/A')}")

                        # Makers info (indie detection)
                        makers = post.get('makers', [])
                        if makers:
                            print(f"\n  Makers ({len(makers)}):")
                            for maker in makers[:3]:
                                print(f"    - {maker.get('name', '?')} (@{maker.get('username', '?')})")

                        results["Get Post Details"] = True
                    else:
                        print(f"  No post details returned")
                        results["Get Post Details"] = False
                else:
                    print("  Could not get a post to look up")
                    results["Get Post Details"] = False
            except Exception as e:
                print(f"  Error: {e}")
                results["Get Post Details"] = False

            # Test 6: Get collections
            print("\n📚 TEST 6: Get Collections")
            print("─" * 40)
            try:
                result = await session.call_tool("get_collections", {
                    "featured": True,
                    "count": 5
                })
                content = result.content[0].text if result.content else "{}"
                data = json.loads(content)
                coll_data = data.get("data", data)

                if coll_data.get("collections"):
                    collections = [c.get("node", c) for c in coll_data["collections"]]
                    print(f"  Found {len(collections)} featured collections:\n")
                    for coll in collections[:5]:
                        print(f"  • {coll.get('name', 'Unknown')}")
                        print(f"    Followers: {coll.get('followersCount', 0)}")
                    results["Get Collections"] = True
                else:
                    print(f"  No collections found")
                    results["Get Collections"] = False
            except Exception as e:
                print(f"  Error: {e}")
                results["Get Collections"] = False

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    for test, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {test}")

    all_passed = all(results.values())
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️ Some tests failed"))

    return all_passed


if __name__ == "__main__":
    asyncio.run(test_product_hunt_mcp())

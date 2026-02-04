import os
from langchain_core.tools import tool
from tavily import TavilyClient


tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use this to find
    trending apps, App Store charts, app rankings, and app news."""

    response = tavily_client.search(
        query=query,
        max_results=10,
        search_depth="advanced",
    )

    results = []
    for r in response.get("results", []):
        results.append(
            f"Title: {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Content: {r['content']}\n"
        )

    return "\n---\n".join(results) if results else "No results found."

RESEARCH_TOOLS = [web_search]

# export to list other tools here: 
# and then insert into graph when needed:
# ex : workflow.add_node(TOOL(REASEACH_TOOLS))
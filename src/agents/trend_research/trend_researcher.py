from config import APP_TRENDS_ANALYZER
from agents.base import run_agent, AgentResults


def build_research_prompt(user_query: str) -> str:
    return (
        "You are tasked with producing a daily Apple App Store trending report.\n\n"
        "STEP 1 — DATA GATHERING:\n"
        "Search the web for today's Apple App Store trending and top charts data. "
        "Look across multiple sources:\n"
        "- Apple App Store top charts (free, paid, top grossing)\n"
        "- App analytics sites (Sensor Tower, AppFigures, data.ai, AppFollow)\n"
        "- Tech news for apps going viral or trending on social media\n"
        "- Any recent App Store features or editorial picks\n\n"
        "STEP 2 — ANALYSIS:\n"
        "For each trending app (aim for 5-10 apps), gather:\n"
        "- App name and developer/publisher\n"
        "- Category (Games, Social, Productivity, Health & Fitness, Entertainment, etc.)\n"
        "- Current chart position and direction (e.g. '#3 Free, up from #15')\n"
        "- Price (free, freemium, paid — include price if paid)\n"
        "- Star rating and approximate number of ratings if available\n"
        "- Why it's trending: new launch, major update, viral TikTok/social moment, "
        "seasonal relevance, controversy, celebrity endorsement, or App Store feature\n\n"
        "STEP 3 — OUTPUT FORMAT:\n"
        "Return a structured report with each app as a block:\n"
        "APP: [Name]\n"
        "DEVELOPER: [Developer]\n"
        "CATEGORY: [Category]\n"
        "RANK: [Position and movement]\n"
        "PRICE: [Free/Paid]\n"
        "RATING: [Stars and count]\n"
        "TRENDING REASON: [One sentence]\n"
        "---\n\n"
        "End with a 'TRENDS SUMMARY' section — 2-3 sentences on overall patterns "
        "(e.g. 'AI apps dominating this week', 'new game genre surging').\n\n"
        f"User focus area: {user_query}\n"
        "Prioritize apps relevant to the user's focus if specified, "
        "but still cover notable movers outside that area."
    )

# async def run_trend_researcher(user_query: str) -> AgentResults:
#     prompt = build_research_prompt(user_query)

#     results = await run_agent(
#         agent_name=APP_TRENDS_ANALYZER.name,
#         prompt=prompt,
#         tools=APP_TRENDS_ANALYZER.tools,
#         system_prompt=APP_TRENDS_ANALYZER.system_prompt,
#         timeout_seconds=APP_TRENDS_ANALYZER.timeout_seconds,
#     )

#     return results

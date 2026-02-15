import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "src")

from workflow.graph import run_workflow
from agents import print_markdown


async def main():
    # run_workflow expects categories (list of strings), mode, and debug
    # For "all categories" use a general mode with broad categories
    final_state = await run_workflow(
        categories=["AI Photo/Video", "Productivity", "Health & Fitness", "Games"],
        mode="general",
        debug=False,
    )

    output = final_state.get("output_to_user", "No output generated.")
    print_markdown(output, title="Daily Alpha")


if __name__ == "__main__":
    asyncio.run(main())

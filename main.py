import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "src")

from workflow.graph import run_workflow
from agents import print_markdown


async def main():
    final_state = await run_workflow(
        user_query="What apps are trending today across all categories?"
    )

    output = final_state.get("output_to_user", "No output generated.")
    print_markdown(output, title="Daily Alpha")


if __name__ == "__main__":
    asyncio.run(main())

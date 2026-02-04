import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "src")

from workflow.graph import run_workflow


async def main():
    final_state = await run_workflow(
        user_query="What apps are trending today across all categories?"
    )
    print(final_state.get("output_to_user", "No output generated."))


if __name__ == "__main__":
    asyncio.run(main())

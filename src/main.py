import asyncio
from workflow import run_workflow
from agents import print_markdown


async def main():
    results = await run_workflow(
        user_query="whats trending today in productivity?"
    )

    # pretty print the markdown output
    print_markdown(results["output_to_user"], title="Daily Alpha")


if __name__ == "__main__":
    asyncio.run(main())

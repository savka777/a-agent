from .workflow import run_workflow

async def main():
    results = await run_workflow(
        user_query="whats trending today in productivity?"
    )

    print(results.output_to_user)

if __name__ == "__main__":
    main()

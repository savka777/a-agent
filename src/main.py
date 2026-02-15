#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# ALPHY - Deep Clone Research Agent
#
# Main entry point for the deep research workflow.
#
# Usage:
#   uv run python src/main.py                   # Interactive mode
#   uv run python src/main.py "plant apps"      # Targeted mode
#   uv run python src/main.py --debug           # Debug mode
# -----------------------------------------------------------------------------

import asyncio
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from cli import (
    show_banner,
    select_categories,
    select_mode,
    get_single_niche,
    parse_args,
    save_report,
    show_progress,
    show_completion,
    show_error,
)
from workflow import run_workflow
from agents import print_markdown


async def run_research(categories: list, mode: str, debug: bool):
    """Run the async research workflow."""
    show_progress("Starting", "Deep research workflow...")

    results = await run_workflow(
        categories=categories,
        mode=mode,
        debug=debug,
    )

    return results


def main():
    """Main entry point for ALPHY."""

    # Parse command line arguments
    args = parse_args()

    # Show banner
    show_banner()

    # Determine mode and categories (all sync operations)
    categories = []
    mode = "general"

    # Check for direct niche argument (targeted mode)
    if args.niche:
        mode = "targeted"
        categories = [args.niche]
        print(f"\n🎯 Targeted research mode: {args.niche}\n")

    # Check for categories argument
    elif args.categories:
        categories = [c.strip() for c in args.categories.split(",") if c.strip()]
        mode = args.mode or "general"
        print(f"\n📋 Categories: {', '.join(categories)}\n")

    # Interactive selection (sync - before entering async context)
    else:
        # Ask for mode
        mode = select_mode()

        if mode == "targeted":
            niche = get_single_niche()
            if not niche:
                print("No niche specified. Exiting.")
                return
            categories = [niche]
        else:
            categories = select_categories()

        if not categories:
            print("No categories selected. Exiting.")
            return

    # Validate we have categories
    if not categories:
        show_error("No categories specified")
        return

    # Show what we're about to do
    print(f"\n🔍 Researching {len(categories)} categor{'y' if len(categories) == 1 else 'ies'}:")
    for cat in categories:
        print(f"   • {cat}")
    print()

    if args.debug:
        print("🐛 Debug mode enabled\n")

    # Run the async workflow
    try:
        results = asyncio.run(run_research(categories, mode, args.debug))

        # Check for errors
        errors = results.get("errors", [])
        if errors:
            print(f"\n⚠️  Warnings during research:")
            for err in errors[:5]:
                print(f"   • {err}")
            print()

        # Save reports
        json_path, md_path = save_report(results, categories)

        # Print the markdown report
        output = results.get("output_to_user", "")
        if output:
            print_markdown(output, title="ALPHY Research Report")

        # Show completion
        show_completion(json_path, md_path)

    except KeyboardInterrupt:
        print("\n\n🛑 Research cancelled by user.")
        sys.exit(1)

    except Exception as e:
        show_error(str(e))
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

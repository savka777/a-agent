#!/usr/bin/env python3
"""
Gold Standard Evaluation Runner

Runs ALPHY workflow for all 10 categories and populates gold_standard.json
with skeleton entries for manual labeling.

Usage:
    uv run python scripts/run_gold_standard.py

Options:
    --parallel    Run categories in parallel (faster but more resource intensive)
    --sequential  Run categories one at a time (default, safer)
    --dry-run     Show what would be run without executing
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

console = Console()

# The 10 categories for gold standard evaluation
CATEGORIES = [
    "AI Writing Tools",
    "Developer Tools & Utilities",
    "Personal Knowledge Management",
    "Screenshot & Screen Recording",
    "Habit & Routine Trackers",
    "Journaling & Mental Wellness",
    "Freelancer & Invoice Tools",
    "No-Code & Automation",
    "Focus & Distraction Blocking",
    "Mac Menu Bar Utilities",
]

GOLD_STANDARD_PATH = Path(__file__).parent.parent / "scorers" / "gold_standard.json"
ALPHY_OUTPUT_DIR = Path(__file__).parent.parent / "alphy"


def load_gold_standard() -> dict:
    """Load existing gold standard or create new one."""
    if GOLD_STANDARD_PATH.exists():
        with open(GOLD_STANDARD_PATH) as f:
            return json.load(f)
    return {
        "version": "1.0",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "pass_thresholds": {
            "min_apps": 6,
            "max_hallucinations": 0,
            "max_broken_links": 1,
            "min_relevance_pct": 80
        },
        "runs": []
    }


def save_gold_standard(data: dict):
    """Save gold standard to file."""
    with open(GOLD_STANDARD_PATH, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"[green]Saved gold standard to {GOLD_STANDARD_PATH}[/green]")


def get_next_run_id(gold_standard: dict) -> str:
    """Generate next run ID."""
    existing_ids = [r["id"] for r in gold_standard.get("runs", [])]
    num = 1
    while f"run_{num:03d}" in existing_ids:
        num += 1
    return f"run_{num:03d}"


def category_to_slug(category: str) -> str:
    """Convert category name to filename slug."""
    slug = category.lower().replace(" ", "-").replace("&", "and")
    return "".join(c if c.isalnum() or c == "-" else "" for c in slug)[:25]


def extract_apps_from_json(json_path: Path) -> list:
    """Extract app names and URLs from ALPHY JSON output."""
    if not json_path.exists():
        return []

    try:
        with open(json_path) as f:
            data = json.load(f)

        apps = []

        # Try to extract from discovered_apps
        if "discovered_apps" in data:
            for app in data["discovered_apps"]:
                apps.append({
                    "name": app.get("name", "Unknown"),
                    "url": app.get("source_url") or app.get("url") or None,
                    "exists": None,
                    "cited": None,
                    "relevant": None,
                    "recent": None,
                    "indie": None,
                    "opportunity_quality": None,
                    "notes": ""
                })

        # Fallback: try apps_researched
        if not apps and "apps_researched" in data:
            for app in data["apps_researched"]:
                apps.append({
                    "name": app.get("name", "Unknown"),
                    "url": app.get("source_url") or app.get("url") or None,
                    "exists": None,
                    "cited": None,
                    "relevant": None,
                    "recent": None,
                    "indie": None,
                    "opportunity_quality": None,
                    "notes": ""
                })

        return apps
    except Exception as e:
        console.print(f"[yellow]Warning: Could not parse {json_path}: {e}[/yellow]")
        return []


async def run_single_category(category: str, progress=None, task_id=None) -> dict:
    """Run ALPHY workflow for a single category."""
    from workflow.graph import run_workflow
    from cli import save_report

    if progress and task_id:
        progress.update(task_id, description=f"[cyan]Running: {category}[/cyan]")

    console.print(f"\n[bold blue]Starting: {category}[/bold blue]")

    try:
        # Run the deep research workflow
        result = await run_workflow(
            categories=[category],
            mode="general",
            debug=False,
        )

        # Save report
        json_path, md_path = save_report(result, [category])

        console.print(f"[green]Completed: {category}[/green]")
        console.print(f"  Output: {md_path}")

        return {
            "success": True,
            "category": category,
            "json_path": json_path,
            "md_path": md_path,
            "result": result
        }

    except Exception as e:
        console.print(f"[red]Failed: {category} - {e}[/red]")
        return {
            "success": False,
            "category": category,
            "error": str(e)
        }
    finally:
        if progress and task_id:
            progress.advance(task_id)


async def run_all_sequential(categories: list) -> list:
    """Run all categories sequentially."""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running evaluations...", total=len(categories))

        for category in categories:
            result = await run_single_category(category, progress, task)
            results.append(result)

    return results


async def run_all_parallel(categories: list, max_concurrent: int = 3) -> list:
    """Run categories in parallel with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_semaphore(category):
        async with semaphore:
            return await run_single_category(category)

    console.print(f"[bold]Running {len(categories)} categories in parallel (max {max_concurrent} concurrent)[/bold]")

    tasks = [run_with_semaphore(cat) for cat in categories]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append({
                "success": False,
                "category": categories[i],
                "error": str(result)
            })
        else:
            processed.append(result)

    return processed


def create_gold_standard_entries(results: list, gold_standard: dict) -> dict:
    """Create gold standard entries from run results."""
    today = datetime.now().strftime("%Y-%m-%d")

    for result in results:
        if not result.get("success"):
            continue

        category = result["category"]
        json_path = result.get("json_path", "")
        md_path = result.get("md_path", "")

        # Extract apps from JSON output
        apps = []
        if json_path and Path(json_path).exists():
            apps = extract_apps_from_json(Path(json_path))

        run_id = get_next_run_id(gold_standard)

        entry = {
            "id": run_id,
            "input_category": category,
            "run_date": today,
            "output_file": md_path,
            "json_file": json_path,
            "pass": None,  # To be filled manually
            "failure_reasons": [],
            "labeled_apps": apps,
            "summary": {
                "total_apps": len(apps),
                "apps_exist": 0,
                "apps_cited": 0,
                "apps_relevant": 0,
                "apps_recent": 0,
                "apps_indie": 0,
                "hallucinations": 0,
                "broken_links": 0
            },
            "labeler_notes": "TODO: Review and label each app"
        }

        gold_standard["runs"].append(entry)

    return gold_standard


def print_summary(results: list):
    """Print summary table of results."""
    table = Table(title="Gold Standard Evaluation Results")
    table.add_column("Category", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Output", style="dim")

    for result in results:
        status = "[green]Success[/green]" if result.get("success") else f"[red]Failed: {result.get('error', 'Unknown')}[/red]"
        output = result.get("md_path", "-")
        table.add_row(result["category"], status, output)

    console.print("\n")
    console.print(table)

    success_count = sum(1 for r in results if r.get("success"))
    console.print(f"\n[bold]Completed: {success_count}/{len(results)} categories[/bold]")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run gold standard evaluations")
    parser.add_argument("--parallel", action="store_true", help="Run categories in parallel")
    parser.add_argument("--sequential", action="store_true", help="Run categories sequentially (default)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be run")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent runs (for parallel mode)")
    parser.add_argument("--categories", type=str, help="Comma-separated list of specific categories to run")

    args = parser.parse_args()

    # Determine which categories to run
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]
    else:
        categories = CATEGORIES

    # Show banner
    console.print(Panel(
        "[bold green]ALPHY Gold Standard Evaluation Runner[/bold green]\n\n"
        f"Categories to evaluate: {len(categories)}\n"
        f"Mode: {'Parallel' if args.parallel else 'Sequential'}\n"
        f"Output: scorers/gold_standard.json",
        title="Gold Standard Builder"
    ))

    if args.dry_run:
        console.print("\n[yellow]DRY RUN - Would execute:[/yellow]")
        for i, cat in enumerate(categories, 1):
            console.print(f"  {i}. {cat}")
        return

    # Load existing gold standard
    gold_standard = load_gold_standard()

    # Run evaluations
    if args.parallel:
        results = asyncio.run(run_all_parallel(categories, args.max_concurrent))
    else:
        results = asyncio.run(run_all_sequential(categories))

    # Create gold standard entries
    gold_standard = create_gold_standard_entries(results, gold_standard)

    # Save gold standard
    save_gold_standard(gold_standard)

    # Print summary
    print_summary(results)

    console.print("\n[bold green]Next steps:[/bold green]")
    console.print("1. Open scorers/gold_standard.json")
    console.print("2. For each run, review labeled_apps and fill in:")
    console.print("   - exists, cited, relevant, recent, indie, opportunity_quality")
    console.print("3. Set 'pass' to true/false based on thresholds")
    console.print("4. Add any failure_reasons if applicable")


if __name__ == "__main__":
    main()

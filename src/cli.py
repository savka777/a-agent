# -----------------------------------------------------------------------------
# ALPHY CLI
#
# Interactive command-line interface for the deep research agent.
# Provides category selection, progress display, and report saving.
# -----------------------------------------------------------------------------

import os
import sys
import argparse
from typing import List, Optional
from datetime import datetime

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


# =============================================================================
# BANNER
# =============================================================================

ALPHY_BANNER = """
    _    _     ____  _   ___   __
   / \\  | |   |  _ \\| | | \\ \\ / /
  / _ \\ | |   | |_) | |_| |\\ V /
 / ___ \\| |___|  __/|  _  | | |
/_/   \\_\\_____|_|   |_| |_| |_|

      Deep Clone Research Agent
"""


# =============================================================================
# PRESET CATEGORIES
# =============================================================================

PRESET_CATEGORIES = [
    "Productivity & Utilities",
    "AI Photo/Video",
    "Health & Fitness",
    "Social & Dating",
    "Casual Games",
    "Finance & Crypto",
    "Education",
    "Food & Recipes",
    "Travel",
    "Music & Audio",
]


# =============================================================================
# CLI FUNCTIONS
# =============================================================================

def show_banner():
    """Display the ALPHY ASCII banner."""
    console = Console()
    console.print(Panel(
        Text(ALPHY_BANNER, style="green"),
        border_style="green",
        padding=(0, 2)
    ))


def select_categories() -> List[str]:
    """
    Interactive category selection with checkboxes.
    Returns list of selected categories.
    """
    # Add custom option at the end
    choices = PRESET_CATEGORIES + ["[Custom] Enter your own niche..."]

    try:
        selected = questionary.checkbox(
            "Select categories to research (space to select, enter to confirm):",
            choices=choices,
            instruction="(Use arrow keys to move, space to select, enter to confirm)"
        ).ask()

        if selected is None:
            # User cancelled (Ctrl+C)
            return []

        # Handle custom input
        final_categories = []
        for s in selected:
            if "[Custom]" in s:
                custom = questionary.text(
                    "Enter custom niche(s) (comma-separated):"
                ).ask()
                if custom:
                    for c in custom.split(","):
                        c = c.strip()
                        if c:
                            final_categories.append(c)
            else:
                final_categories.append(s)

        return final_categories

    except KeyboardInterrupt:
        return []


def get_single_niche() -> Optional[str]:
    """
    Prompt for a single niche (targeted mode).
    """
    try:
        niche = questionary.text(
            "Enter the niche to research deeply:",
            instruction="(e.g., 'plant identifier apps', 'meditation apps')"
        ).ask()
        return niche
    except KeyboardInterrupt:
        return None


def select_mode() -> str:
    """
    Let user choose between general and targeted mode.
    """
    try:
        mode = questionary.select(
            "Select research mode:",
            choices=[
                questionary.Choice(
                    "General - Scan multiple categories, find best opportunities",
                    value="general"
                ),
                questionary.Choice(
                    "Targeted - Deep dive into one specific niche (8+ apps)",
                    value="targeted"
                ),
            ]
        ).ask()
        return mode or "general"
    except KeyboardInterrupt:
        return "general"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ALPHY - Deep Clone Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python src/main.py                      # Interactive mode
  uv run python src/main.py "plant apps"         # Targeted mode for specific niche
  uv run python src/main.py --debug              # Enable verbose logging
  uv run python src/main.py --categories "AI,Games"  # Skip category selection
"""
    )

    parser.add_argument(
        "niche",
        nargs="?",
        default=None,
        help="Optional: specific niche for targeted research"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging"
    )

    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated list of categories (skips interactive selection)"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["general", "targeted"],
        default=None,
        help="Research mode: general or targeted"
    )

    return parser.parse_args()


# =============================================================================
# REPORT SAVING
# =============================================================================

def save_report(results: dict, categories: List[str]) -> tuple[str, str]:
    """
    Save the research report to files.

    Returns:
        Tuple of (json_path, markdown_path)
    """
    import json

    # Create alphy directory if it doesn't exist
    os.makedirs("alphy", exist_ok=True)

    # Generate filename: MM-DD-YY-alphy-{niche}
    date_str = datetime.now().strftime("%m-%d-%y")

    # Create slug from categories
    if categories:
        niche_slug = categories[0].replace(" ", "-").replace("&", "and").lower()[:20]
    else:
        niche_slug = "general"

    # Clean up slug
    niche_slug = "".join(c if c.isalnum() or c == "-" else "" for c in niche_slug)

    filename = f"{date_str}-alphy-{niche_slug}"

    # Save JSON
    json_path = f"alphy/{filename}.json"
    with open(json_path, "w") as f:
        json.dump(results.get("json_output", {}), f, indent=2, default=str)

    # Save Markdown report
    md_path = f"alphy/{filename}.md"
    with open(md_path, "w") as f:
        f.write(results.get("output_to_user", "No report generated."))

    return json_path, md_path


# =============================================================================
# PROGRESS DISPLAY
# =============================================================================

def show_progress(phase: str, detail: str = ""):
    """Show progress indicator."""
    console = Console()
    phase_emoji = {
        "init": "🚀",
        "planning": "📋",
        "discovery": "🔍",
        "deep_research": "🔬",
        "reflection": "🤔",
        "pattern_extraction": "🧬",
        "synthesis": "✍️",
    }
    emoji = phase_emoji.get(phase.lower(), "⏳")
    console.print(f"{emoji} [bold]{phase}[/bold] {detail}")


def show_completion(json_path: str, md_path: str):
    """Show completion message with file paths."""
    console = Console()
    console.print()
    console.print(Panel(
        f"[green]✅ Research complete![/green]\n\n"
        f"📄 Markdown report: [cyan]{md_path}[/cyan]\n"
        f"📊 JSON data: [cyan]{json_path}[/cyan]",
        title="ALPHY Results",
        border_style="green"
    ))


def show_error(message: str):
    """Show error message."""
    console = Console()
    console.print(f"[red]❌ Error: {message}[/red]")

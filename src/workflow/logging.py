# -----------------------------------------------------------------------------
# ALPHY Debug Logging
#
# Provides real-time status display during research workflow.
# Used when --debug flag is enabled.
# -----------------------------------------------------------------------------

from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text


class AlphyLogger:
    """
    Debug logger that shows real-time research progress.

    Usage:
        logger = AlphyLogger(debug=True)
        logger.set_phase("DISCOVERY")
        logger.agent_status("discovery_1", "Searching 'viral apps reddit'")
        logger.update_progress(5, 30)
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.console = Console()
        self.current_phase = ""
        self.active_agents: Dict[str, str] = {}
        self.progress = (0, 0)  # (done, total)
        self._live: Optional[Live] = None

    def set_phase(self, phase: str):
        """Set the current workflow phase."""
        self.current_phase = phase
        if self.debug:
            self.console.print(f"📍 Phase: [bold cyan]{phase}[/bold cyan]")

    def agent_status(self, agent_id: str, status: str):
        """Update status for an active agent."""
        self.active_agents[agent_id] = status
        if self.debug:
            self.console.print(f"   🤖 {agent_id}: {status}")

    def agent_complete(self, agent_id: str, result: str = ""):
        """Mark an agent as complete."""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
        if self.debug and result:
            self.console.print(f"   ✅ {agent_id}: {result}")

    def update_progress(self, done: int, total: int):
        """Update progress counters."""
        self.progress = (done, total)
        if self.debug:
            self.console.print(f"📊 Progress: {done}/{total} apps")

    def log_tool_call(self, tool_name: str, query: str):
        """Log a tool call."""
        if self.debug:
            short_query = query[:50] + "..." if len(query) > 50 else query
            self.console.print(f"   🔧 {tool_name}: {short_query}")

    def log_app_found(self, app_name: str, category: str = ""):
        """Log when an app is discovered."""
        if self.debug:
            cat_str = f" ({category})" if category else ""
            self.console.print(f"   🎯 Found: {app_name}{cat_str}")

    def log_error(self, message: str):
        """Log an error."""
        self.console.print(f"   [red]❌ Error: {message}[/red]")

    def log_warning(self, message: str):
        """Log a warning."""
        if self.debug:
            self.console.print(f"   [yellow]⚠️  {message}[/yellow]")

    def show_status_panel(self):
        """Show a rich status panel (for live updates)."""
        if not self.debug:
            return

        # Build status table
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        table.add_row("Phase", self.current_phase)
        table.add_row("Progress", f"{self.progress[0]}/{self.progress[1]} apps")
        table.add_row("Active Agents", str(len(self.active_agents)))

        # Add active agents
        for agent_id, status in list(self.active_agents.items())[:5]:
            table.add_row(f"  └─ {agent_id}", status)

        self.console.print(Panel(table, title="ALPHY Status", border_style="green"))

    def start_live(self):
        """Start live updating display."""
        if self.debug:
            self._live = Live(
                self._build_status(),
                console=self.console,
                refresh_per_second=4,
            )
            self._live.start()

    def stop_live(self):
        """Stop live updating display."""
        if self._live:
            self._live.stop()
            self._live = None

    def update_live(self):
        """Update the live display."""
        if self._live:
            self._live.update(self._build_status())

    def _build_status(self) -> Panel:
        """Build the status panel for live display."""
        lines = []
        lines.append(f"📍 Phase: [bold]{self.current_phase}[/bold]")
        lines.append(f"📊 Progress: {self.progress[0]}/{self.progress[1]} apps")

        if self.active_agents:
            lines.append(f"🤖 Active agents: {len(self.active_agents)}")
            for agent_id, status in list(self.active_agents.items())[:5]:
                lines.append(f"   ├─ {agent_id}: {status}")

        return Panel("\n".join(lines), title="ALPHY Status", border_style="green")


# Global logger instance
_logger: Optional[AlphyLogger] = None


def get_logger(debug: bool = False) -> AlphyLogger:
    """Get or create the global logger."""
    global _logger
    if _logger is None:
        _logger = AlphyLogger(debug=debug)
    return _logger


def set_debug(enabled: bool):
    """Enable or disable debug mode."""
    logger = get_logger()
    logger.debug = enabled

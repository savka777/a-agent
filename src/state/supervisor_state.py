"""Supervisor state for the ALPHY workflow."""

from typing import TypedDict, Literal, Annotated
from operator import add

from langchain_core.messages import BaseMessage

from .schemas import (
    ResearchTask,
    ResearchResult,
    FailedTask,
    Scratchpad,
)


# Custom reducers for state updates
def merge_scratchpad(current: Scratchpad | None, update: Scratchpad | None) -> Scratchpad:
    """Merge scratchpad updates, combining lists and dicts."""
    if current is None:
        return update or Scratchpad()
    if update is None:
        return current

    return Scratchpad(
        discovered_apps=current.discovered_apps + [
            app for app in update.discovered_apps
            if app.app_id not in {a.app_id for a in current.discovered_apps}
        ],
        researched_apps={**current.researched_apps, **update.researched_apps},
        product_hunt_launches=current.product_hunt_launches + [
            p for p in update.product_hunt_launches
            if p.id not in {ph.id for ph in current.product_hunt_launches}
        ],
        patterns=list(set(current.patterns + update.patterns)),
        user_refinements=current.user_refinements + update.user_refinements,
    )


def dedupe_tasks(current: list[ResearchTask], update: list[ResearchTask]) -> list[ResearchTask]:
    """Deduplicate tasks by ID."""
    current_ids = {t.id for t in current}
    return current + [t for t in update if t.id not in current_ids]


def dedupe_results(current: list[ResearchResult], update: list[ResearchResult]) -> list[ResearchResult]:
    """Deduplicate results by task_id."""
    current_ids = {r.task_id for r in current}
    return current + [r for r in update if r.task_id not in current_ids]


# Intent types
Intent = Literal["explore", "validate", "compare", "deep_dive"]


# Worker status tracking
class WorkerStatus(TypedDict):
    """Status of a parallel worker."""
    worker_id: str
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: str
    error: str | None


class SupervisorState(TypedDict, total=False):
    """
    Main state for the ALPHY supervisor workflow.

    This state flows through the LangGraph workflow and is updated
    by each node.
    """

    # --- User Interaction ---
    user_query: str
    messages: Annotated[list[BaseMessage], add]

    # --- Planning ---
    intent: Intent
    plan: list[ResearchTask]
    plan_approved: bool

    # --- Execution ---
    scratchpad: Annotated[Scratchpad, merge_scratchpad]
    pending_tasks: Annotated[list[ResearchTask], dedupe_tasks]
    active_workers: dict[str, WorkerStatus]

    # --- Results ---
    completed_results: Annotated[list[ResearchResult], dedupe_results]
    failed_tasks: Annotated[list[FailedTask], add]

    # --- Control ---
    iteration_count: int
    max_iterations: int  # default 3
    current_phase: Literal[
        "init",
        "planning",
        "awaiting_approval",
        "researching",
        "evaluating",
        "synthesizing",
        "awaiting_followup",
        "complete",
    ]

    # --- Output ---
    final_response: str
    report_path: str | None


def create_initial_state(user_query: str) -> SupervisorState:
    """Create initial state for a new research session."""
    return SupervisorState(
        user_query=user_query,
        messages=[],
        intent="explore",
        plan=[],
        plan_approved=False,
        scratchpad=Scratchpad(),
        pending_tasks=[],
        active_workers={},
        completed_results=[],
        failed_tasks=[],
        iteration_count=0,
        max_iterations=3,
        current_phase="init",
        final_response="",
        report_path=None,
    )

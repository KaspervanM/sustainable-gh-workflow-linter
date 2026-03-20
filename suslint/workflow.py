from __future__ import annotations

from typing import Any, Iterator

from ruamel.yaml.comments import CommentedMap


def iter_jobs(workflow: CommentedMap) -> Iterator[tuple[str, CommentedMap]]:
    jobs = workflow.get("jobs")

    if not isinstance(jobs, CommentedMap):
        return

    for job_name, job in jobs.items():
        if isinstance(job, CommentedMap):
            yield str(job_name), job


def get_event_trigger(workflow: CommentedMap, event_name: str) -> Any:
    triggers = workflow.get("on")

    if triggers == event_name:
        return True

    if not isinstance(triggers, CommentedMap):
        return None

    trigger = triggers.get(event_name)
    if trigger is None and event_name in triggers:
        return True

    return trigger


def has_branch_filters(trigger: Any) -> bool:
    return isinstance(trigger, CommentedMap) and bool(
        trigger.get("branches") or trigger.get("branches-ignore")
    )


def iter_steps(job: CommentedMap) -> Iterator[tuple[int, CommentedMap]]:
    steps = job.get("steps")

    if not isinstance(steps, list):
        return

    for index, step in enumerate(steps):
        if isinstance(step, CommentedMap):
            yield index, step


def is_checkout_step(step: CommentedMap) -> bool:
    uses = step.get("uses")
    return isinstance(uses, str) and uses.strip().lower().startswith("actions/checkout@")


def get_step_name(step: CommentedMap, fallback_index: int) -> str:
    name = step.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return f"steps[{fallback_index}]"


def step_uses_action(step: CommentedMap, action_prefix: str) -> bool:
    uses = step.get("uses")
    return isinstance(uses, str) and uses.strip().lower().startswith(action_prefix.lower())


def step_run_text(step: CommentedMap) -> str | None:
    run = step.get("run")
    return run if isinstance(run, str) else None


def normalize_needs(job: CommentedMap) -> list[str]:
    needs = job.get("needs")

    if isinstance(needs, str):
        return [needs]

    if isinstance(needs, list):
        return [item for item in needs if isinstance(item, str)]

    return []


def job_uses_needs_context(job: CommentedMap) -> bool:
    def contains_needs_ref(value: Any) -> bool:
        if isinstance(value, str):
            return "needs." in value
        if isinstance(value, CommentedMap):
            return any(contains_needs_ref(v) for v in value.values())
        if isinstance(value, list):
            return any(contains_needs_ref(v) for v in value)
        return False

    return contains_needs_ref(job)


def get_strategy_matrix(job: CommentedMap) -> CommentedMap | None:
    strategy = job.get("strategy")
    if not isinstance(strategy, CommentedMap):
        return None

    matrix = strategy.get("matrix")
    if isinstance(matrix, CommentedMap):
        return matrix

    return None
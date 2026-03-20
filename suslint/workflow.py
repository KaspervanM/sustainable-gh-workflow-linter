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

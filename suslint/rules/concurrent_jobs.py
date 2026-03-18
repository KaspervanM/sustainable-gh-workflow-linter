from __future__ import annotations

from typing import Any, Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import iter_jobs


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    return False


def _has_effective_concurrency(mapping: CommentedMap) -> bool:
    concurrency = mapping.get("concurrency")

    if not isinstance(concurrency, CommentedMap):
        return False

    group = concurrency.get("group")
    cancel_in_progress = concurrency.get("cancel-in-progress")

    return _is_non_empty_string(group) and _is_truthy(cancel_in_progress)


class ConcurrentJobsRule:
    id = "SUS010"
    description = "Jobs should avoid concurrent duplicate runs by using concurrency cancellation"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Add workflow-level or job-level concurrency with a group and "
            "cancel-in-progress so duplicate runs are cancelled instead of running in parallel."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")
        if not isinstance(jobs, CommentedMap):
            return

        if _has_effective_concurrency(workflow):
            return

        for job_name, job in iter_jobs(workflow):
            if _has_effective_concurrency(job):
                continue

            yield Issue(
                rule_id=self.id,
                message=(
                    f"job '{job_name}' has no effective concurrency control and may run "
                    "concurrently with duplicate executions"
                ),
                location=Location(f"jobs.{job_name}", *pos(jobs, job_name)),
            )


RULE: Rule = ConcurrentJobsRule()
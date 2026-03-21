from __future__ import annotations

from typing import Iterable, Any

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import iter_jobs, iter_steps


def _get_runs_on(job: CommentedMap) -> Any:
    return job.get("runs-on")


def _count_steps(job: CommentedMap) -> int:
    return sum(1 for _ in iter_steps(job))


def _is_small_job(job: CommentedMap) -> bool:
    return _count_steps(job) < 3


def _is_sequential(prev_job: CommentedMap, job: CommentedMap) -> bool:
    needs = job.get("needs")

    if isinstance(needs, str):
        return needs == prev_job
    if isinstance(needs, list):
        return len(needs) == 1 and needs[0] == prev_job

    return False

def _build_dependency_graph(jobs: CommentedMap) -> dict[str, list[str]]:
    dependents: dict[str, list[str]] = {}

    for job_name, job in jobs.items():
        if not isinstance(job, CommentedMap):
            continue

        needs = job.get("needs")

        if isinstance(needs, str):
            dependents.setdefault(needs, []).append(job_name)
        elif isinstance(needs, list):
            for dep in needs:
                if isinstance(dep, str):
                    dependents.setdefault(dep, []).append(job_name)

    return dependents

class SequentialSmallJobsRule:
    id = "SUS008"
    description = "Sequential small jobs on the same runner should be merged"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Merge small sequential jobs running on the same environment into a single job "
            "to reduce runner startup overhead and CI minutes."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")
        if not isinstance(jobs, CommentedMap):
            return

        # preserve order
        job_items = list(iter_jobs(workflow))
        dependents = _build_dependency_graph(jobs)

        for i in range(1, len(job_items)):
            prev_name, prev_job = job_items[i - 1]
            curr_name, curr_job = job_items[i]

            if not isinstance(prev_job, CommentedMap) or not isinstance(curr_job, CommentedMap):
                continue

            # must be sequential via needs (already exists)
            if not _is_sequential(prev_name, curr_job):
                continue

            # ensure it's a linear chain (no fan-out)
            if len(dependents.get(prev_name, [])) != 1:
                continue

            # same runner
            if _get_runs_on(prev_job) != _get_runs_on(curr_job):
                continue

            # both small
            if not (_is_small_job(prev_job) and _is_small_job(curr_job)):
                continue

            yield Issue(
                rule_id=self.id,
                message=(
                    f"jobs '{prev_name}' and '{curr_name}' are small, sequential, and run on the same "
                    f"environment; consider merging them to reduce CI overhead"
                ),
                location=Location(f"jobs.{curr_name}", *pos(jobs, curr_name)),
            )


RULE: Rule = SequentialSmallJobsRule()
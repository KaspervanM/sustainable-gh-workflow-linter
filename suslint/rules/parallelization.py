from __future__ import annotations

from typing import Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import (
    iter_jobs,
    iter_steps,
    job_uses_needs_context,
    normalize_needs,
    step_uses_action,
)


def _job_downloads_artifacts(job: CommentedMap) -> bool:
    for _, step in iter_steps(job):
        if step_uses_action(step, "actions/download-artifact@"):
            return True
    return False


class ParallelizationRule:
    id = "SUS006"
    description = "Jobs should not be serialized with needs unless they actually depend on earlier jobs"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Remove unnecessary needs dependencies so independent jobs can run in parallel. "
            "Keep needs only when the job consumes artifacts, outputs, or other results from earlier jobs."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")
        if not isinstance(jobs, CommentedMap):
            return

        for job_name, job in iter_jobs(workflow):
            needs = normalize_needs(job)
            if not needs:
                continue

            if _job_downloads_artifacts(job):
                continue

            if job_uses_needs_context(job):
                continue

            yield Issue(
                rule_id=self.id,
                message=(
                    f"job '{job_name}' uses needs={needs} but does not appear to consume artifacts "
                    "or outputs from upstream jobs and may be unnecessarily serialized"
                ),
                location=Location(f"jobs.{job_name}", *pos(jobs, job_name)),
            )


RULE: Rule = ParallelizationRule()
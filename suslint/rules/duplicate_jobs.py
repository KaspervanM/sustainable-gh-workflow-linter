from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import iter_jobs, iter_steps, step_run_text, step_uses_action


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _job_signature(job: CommentedMap) -> tuple:
    """
    Create a comparable signature for a job based on its steps.
    Includes both `run` commands and `uses` actions.
    """
    signature: list[str] = []

    for _, step in iter_steps(job):
        run_text = step_run_text(step)
        if run_text:
            signature.append(f"run:{_normalize(run_text)}")
            continue

        # fallback to action usage
        if isinstance(step, CommentedMap):
            uses = step.get("uses")
            if isinstance(uses, str):
                signature.append(f"uses:{_normalize(uses)}")

    return tuple(signature)


class DuplicateJobsRule:
    id = "SUS004"
    description = "Duplicate jobs with identical steps should be consolidated"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Merge identical jobs "
            "to avoid redundant execution."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")
        if not isinstance(jobs, CommentedMap):
            return

        signature_to_jobs: dict[tuple, list[str]] = defaultdict(list)

        for job_name, job in iter_jobs(workflow):
            sig = _job_signature(job)
            if sig:
                signature_to_jobs[sig].append(job_name)

        for job_names in signature_to_jobs.values():
            if len(job_names) < 2:
                continue

            first_job = job_names[0]
            for duplicate_job in job_names[1:]:
                yield Issue(
                    rule_id=self.id,
                    message=(
                        f"job '{duplicate_job}' duplicates the steps of job '{first_job}'"
                    ),
                    location=Location(f"jobs.{duplicate_job}", *pos(jobs, duplicate_job)),
                )


RULE: Rule = DuplicateJobsRule()
from typing import Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import iter_jobs


class JobTimeoutRule:
    id = "SUS002"
    description = "Jobs should define timeout-minutes to prevent stuck runners"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation="Add timeout-minutes to each job to prevent long-running or stuck runners.",
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")

        if not isinstance(jobs, CommentedMap):
            return

        for job_name, job in iter_jobs(workflow):
            if "timeout-minutes" not in job:
                yield Issue(
                    rule_id=self.id,
                    message=f"job '{job_name}' has no timeout-minutes",
                    location=Location(f"jobs.{job_name}", *pos(jobs, job_name)),
                )


RULE: Rule = JobTimeoutRule()

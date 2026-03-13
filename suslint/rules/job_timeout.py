from typing import Iterable
from ruamel.yaml.comments import CommentedMap


class JobTimeoutRule:
    id = "SUS001"
    description = "Jobs should define timeout-minutes to prevent stuck runners"

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs", {})

        if not isinstance(jobs, CommentedMap):
            return

        for job_name, job in jobs.items():
            if not isinstance(job, CommentedMap):
                continue
            
            if "timeout-minutes" not in job:
                yield Issue(
                    rule_id=self.id,
                    message=f"job '{job_name}' has no timeout-minutes",
                    location=f"jobs.{job_name}",
                )


RULE: Rule = JobTimeoutRule()
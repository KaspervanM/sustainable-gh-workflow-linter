from __future__ import annotations

from typing import Any, Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import get_step_name, is_checkout_step, iter_jobs, iter_steps


def _is_shallow_fetch_depth(value: Any) -> bool:
    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped) == 1

    return False


class ShallowCloneRule:
    id = "SUS007"
    description = "Checkout steps should use shallow clones when full history is not needed"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Set with.fetch-depth: 1 on actions/checkout steps unless full git history is required."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        for job_name, job in iter_jobs(workflow):
            for step_index, step in iter_steps(job):
                if not is_checkout_step(step):
                    continue

                with_block = step.get("with")
                fetch_depth = None

                if isinstance(with_block, CommentedMap):
                    fetch_depth = with_block.get("fetch-depth")

                if _is_shallow_fetch_depth(fetch_depth):
                    continue

                step_name = get_step_name(step, step_index)
                yield Issue(
                    rule_id=self.id,
                    message=(
                        f"job '{job_name}' checkout step '{step_name}' does not use fetch-depth: 1"
                    ),
                    location=Location(
                        f"jobs.{job_name}.steps[{step_index}]",
                        *pos(job, "steps"),
                    ),
                )


RULE: Rule = ShallowCloneRule()
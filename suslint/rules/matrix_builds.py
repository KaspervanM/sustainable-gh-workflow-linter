from __future__ import annotations

from math import prod
from typing import Any, Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import get_strategy_matrix, iter_jobs


MAX_MATRIX_COMBINATIONS = 4
MATRIX_META_KEYS = {"include", "exclude"}


def _count_axis_values(value: Any) -> int | None:
    if isinstance(value, list):
        return len(value)

    return None


def _estimate_matrix_combinations(matrix: CommentedMap) -> int | None:
    axis_sizes: list[int] = []

    for key, value in matrix.items():
        if str(key) in MATRIX_META_KEYS:
            continue

        axis_size = _count_axis_values(value)
        if axis_size is None:
            return None

        axis_sizes.append(axis_size)

    include_entries = matrix.get("include")
    if axis_sizes:
        return prod(axis_sizes)

    if isinstance(include_entries, list):
        return len(include_entries)

    return None


class MatrixBuildsRule:
    id = "SUS009"
    description = "Large matrix builds should be reduced to the necessary combinations"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Reduce matrix size to the minimum necessary combinations or split rarely needed "
            "targets into separate workflows."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")
        if not isinstance(jobs, CommentedMap):
            return

        for job_name, job in iter_jobs(workflow):
            matrix = get_strategy_matrix(job)
            if matrix is None:
                continue

            combinations = _estimate_matrix_combinations(matrix)
            if combinations is None:
                continue

            if combinations <= MAX_MATRIX_COMBINATIONS:
                continue

            yield Issue(
                rule_id=self.id,
                message=(
                    f"job '{job_name}' defines a matrix with {combinations} combinations, "
                    f"which may create excessive runner usage"
                ),
                location=Location(f"jobs.{job_name}.strategy.matrix", *pos(job, "strategy")),
            )


RULE: Rule = MatrixBuildsRule()
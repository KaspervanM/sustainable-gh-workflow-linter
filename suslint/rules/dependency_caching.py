from __future__ import annotations

import re
from typing import Any, Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import iter_jobs, iter_steps


INSTALL_PATTERNS = [
    re.compile(r"\bnpm\s+ci\b"),
    re.compile(r"\bnpm\s+install\b"),
    re.compile(r"\byarn\s+install\b"),
    re.compile(r"\bpnpm\s+install\b"),
    re.compile(r"\bpip\s+install\b"),
    re.compile(r"\bpipenv\s+install\b"),
    re.compile(r"\bpoetry\s+install\b"),
    re.compile(r"\bbundle\s+install\b"),
    re.compile(r"\bmvn\b.*\b(install|verify|test|package)\b"),
    re.compile(r"\bgradle\b.*\b(build|test|assemble)\b"),
    re.compile(r"\bgradlew\b.*\b(build|test|assemble)\b"),
]


def _normalize_action_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _string_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, bool):
        return "true" if value else "false"
    return ""


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return False


def _step_installs_dependencies(step: CommentedMap) -> bool:
    run_value = step.get("run")
    if not isinstance(run_value, str):
        return False

    normalized = run_value.lower()
    return any(pattern.search(normalized) for pattern in INSTALL_PATTERNS)


def _step_enables_cache(step: CommentedMap) -> bool:
    uses = _normalize_action_name(step.get("uses"))
    with_block = step.get("with")

    if uses.startswith("actions/cache@") or uses.startswith("actions/cache/restore@") or uses.startswith("actions/cache/save@"):
        return True

    if not isinstance(with_block, CommentedMap):
        return False

    if uses.startswith("actions/setup-node@"):
        return bool(_string_value(with_block.get("cache")))

    if uses.startswith("actions/setup-python@"):
        return bool(_string_value(with_block.get("cache")))

    if uses.startswith("actions/setup-java@"):
        return bool(_string_value(with_block.get("cache")))

    if uses.startswith("ruby/setup-ruby@"):
        return _is_truthy(with_block.get("bundler-cache"))

    return False


class DependencyCachingRule:
    id = "SUS003"
    description = "Jobs that install dependencies should use caching"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Add dependency caching with actions/cache or enable built-in caching "
            "in setup actions such as setup-node, setup-python, setup-java, or ruby/setup-ruby."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")

        if not isinstance(jobs, CommentedMap):
            return

        for job_name, job in iter_jobs(workflow):
            installs_dependencies = False
            has_cache = False

            for _, step in iter_steps(job):
                if _step_installs_dependencies(step):
                    installs_dependencies = True

                if _step_enables_cache(step):
                    has_cache = True

            if installs_dependencies and not has_cache:
                yield Issue(
                    rule_id=self.id,
                    message=(
                        f"job '{job_name}' installs dependencies without using dependency caching"
                    ),
                    location=Location(f"jobs.{job_name}", *pos(jobs, job_name)),
                )


RULE: Rule = DependencyCachingRule()
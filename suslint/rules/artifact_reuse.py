from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import iter_jobs, iter_steps, step_run_text, step_uses_action


BUILD_SIGNATURE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("npm-build", re.compile(r"\bnpm\s+run\s+build\b")),
    ("yarn-build", re.compile(r"\byarn\s+build\b")),
    ("pnpm-build", re.compile(r"\bpnpm\s+build\b")),
    ("python-build", re.compile(r"\bpython(\d+(\.\d+)*)?\s+-m\s+build\b")),
    ("maven-package", re.compile(r"\bmvn\b.*\b(package|install)\b")),
    ("gradle-build", re.compile(r"\bgradle\b.*\b(build|assemble)\b")),
    ("gradlew-build", re.compile(r"\bgradlew\b.*\b(build|assemble)\b")),
    ("dotnet-build", re.compile(r"\bdotnet\s+(build|publish)\b")),
    ("cargo-build", re.compile(r"\bcargo\s+build\b")),
    ("go-build", re.compile(r"\bgo\s+build\b")),
    ("make-build", re.compile(r"\bmake\s+build\b")),
    ("cmake-build", re.compile(r"\bcmake\s+--build\b")),
    ("pyinstaller", re.compile(r"\bpyinstaller\b")),
]


@dataclass(frozen=True)
class BuildOccurrence:
    job_name: str
    signature: str


def _normalize_run_text(value: str) -> str:
    return " ".join(value.lower().split())


def _detect_build_signatures(job: CommentedMap) -> set[str]:
    signatures: set[str] = set()

    for _, step in iter_steps(job):
        run_text = step_run_text(step)
        if not run_text:
            continue

        normalized = _normalize_run_text(run_text)

        for signature, pattern in BUILD_SIGNATURE_PATTERNS:
            if pattern.search(normalized):
                signatures.add(signature)

    return signatures


def _workflow_uses_artifact_reuse(workflow: CommentedMap) -> bool:
    has_upload = False
    has_download = False

    for _, job in iter_jobs(workflow):
        for _, step in iter_steps(job):
            if step_uses_action(step, "actions/upload-artifact@"):
                has_upload = True
            if step_uses_action(step, "actions/download-artifact@"):
                has_download = True

    return has_upload and has_download


class ArtifactReuseRule:
    id = "SUS005"
    description = "Repeated build jobs should reuse artifacts instead of rebuilding them"
    metadata = RuleMetadata(
        severity="warning",
        category="runner-efficiency",
        remediation=(
            "Upload build outputs in one job and download them in later jobs with "
            "actions/upload-artifact and actions/download-artifact instead of rebuilding them."
        ),
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        jobs = workflow.get("jobs")
        if not isinstance(jobs, CommentedMap):
            return

        if _workflow_uses_artifact_reuse(workflow):
            return

        signature_to_jobs: dict[str, list[str]] = defaultdict(list)

        for job_name, job in iter_jobs(workflow):
            signatures = _detect_build_signatures(job)
            for signature in signatures:
                signature_to_jobs[signature].append(job_name)

        for signature, job_names in signature_to_jobs.items():
            if len(job_names) < 2:
                continue

            first_job = job_names[0]
            for duplicate_job in job_names[1:]:
                yield Issue(
                    rule_id=self.id,
                    message=(
                        f"job '{duplicate_job}' appears to rebuild '{signature}' outputs already "
                        f"built in job '{first_job}' without artifact reuse"
                    ),
                    location=Location(f"jobs.{duplicate_job}", *pos(jobs, duplicate_job)),
                )


RULE: Rule = ArtifactReuseRule()
from pathlib import Path

import pytest

from suslint.core import LintError, lint, load_rules


def test_load_rules_discovers_expected_rules() -> None:
    rule_ids = {rule.id for rule in load_rules()}

    assert rule_ids == {"SUS001", "SUS002"}


def test_lint_reports_job_timeout_with_location(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    issues = lint(workflow, load_rules())

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS001"
    assert issues[0].message == "job 'build' has no timeout-minutes"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 5
    assert issues[0].location.col == 3


def test_lint_reports_push_without_branch_filters(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n",
        encoding="utf-8",
    )

    issues = lint(workflow, load_rules())

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS002"
    assert issues[0].message == "Workflow triggers on push to all branches. Add branch filters."
    assert issues[0].location is not None
    assert issues[0].location.trail == "on.push"
    assert issues[0].location.line == 3
    assert issues[0].location.col == 3


def test_lint_passes_when_workflow_has_timeout_and_branch_filters(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "    branches:\n"
        "      - main\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n",
        encoding="utf-8",
    )

    issues = lint(workflow, load_rules())

    assert issues == []


def test_lint_raises_clean_error_for_non_mapping_top_level_document(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("- item\n", encoding="utf-8")

    with pytest.raises(LintError, match="mapping at the top level"):
        lint(workflow, load_rules())

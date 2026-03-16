from pathlib import Path

import pytest

from suslint.core import LintError, count_affected_files, count_issues, lint, lint_path, load_rules


def test_load_rules_discovers_expected_rules() -> None:
    rules = load_rules()
    rule_ids = [rule.id for rule in rules]

    assert rule_ids == ["SUS001", "SUS002"]
    assert rules[0].metadata.severity == "warning"
    assert rules[0].metadata.category
    assert rules[0].metadata.remediation


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


def test_lint_path_returns_error_result_for_invalid_yaml(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("on:\n  push: [\n", encoding="utf-8")

    result = lint_path(workflow, load_rules())

    assert result.error is not None
    assert result.issues == []
    assert "failed to parse YAML" in result.error


def test_count_helpers_account_for_errors_and_issues(tmp_path: Path) -> None:
    good_workflow = tmp_path / "good.yml"
    bad_workflow = tmp_path / "bad.yml"
    invalid_workflow = tmp_path / "invalid.yml"

    good_workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n",
        encoding="utf-8",
    )
    bad_workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    invalid_workflow.write_text("on:\n  push: [\n", encoding="utf-8")

    results = [
        lint_path(good_workflow, load_rules()),
        lint_path(bad_workflow, load_rules()),
        lint_path(invalid_workflow, load_rules()),
    ]

    assert count_issues(results) == 3
    assert count_affected_files(results) == 2

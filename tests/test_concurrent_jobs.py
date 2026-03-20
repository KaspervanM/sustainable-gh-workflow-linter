from pathlib import Path

from suslint.core import lint
from suslint.rules.concurrent_jobs import RULE


def test_reports_job_without_workflow_or_job_concurrency(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS010"
    assert issues[0].message == (
        "job 'build' has no effective concurrency control and may run concurrently with duplicate executions"
    )
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 5
    assert issues[0].location.col == 3


def test_does_not_report_when_workflow_level_concurrency_is_present(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "concurrency:\n"
        "  group: ci-${{ github.workflow }}-${{ github.ref }}\n"
        "  cancel-in-progress: true\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_job_level_concurrency_is_present(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    concurrency:\n"
        "      group: build-${{ github.ref }}\n"
        "      cancel-in-progress: true\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_reports_only_jobs_missing_job_level_concurrency_when_no_workflow_concurrency(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    concurrency:\n"
        "      group: build-${{ github.ref }}\n"
        "      cancel-in-progress: true\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS010"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.test"


def test_reports_when_concurrency_exists_but_cancel_in_progress_is_missing(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    concurrency:\n"
        "      group: build-${{ github.ref }}\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS010"


def test_reports_when_concurrency_exists_but_group_is_missing(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    concurrency:\n"
        "      cancel-in-progress: true\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS010"
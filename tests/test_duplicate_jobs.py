from pathlib import Path

from suslint.core import lint
from suslint.rules.duplicate_jobs import RULE


def test_reports_duplicate_jobs_with_identical_steps(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo hello\n"
        "      - uses: actions/checkout@v5\n"
        "  copy:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo hello\n"
        "      - uses: actions/checkout@v5\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS004"
    assert issues[0].message == (
        "job 'copy' duplicates the steps of job 'build'"
    )
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.copy"


def test_does_not_report_when_jobs_are_different(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  job1:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo hello\n"
        "  job2:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo world\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_normalization_ignores_whitespace_and_case(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  job1:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo   HELLO\n"
        "  job2:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run:   echo hello  \n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.job2"


def test_reports_multiple_duplicates_against_first(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  base:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: make build\n"
        "  dup1:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: make build\n"
        "  dup2:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: make build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 2
    assert [i.location.trail for i in issues if i.location is not None] == [
        "jobs.dup1",
        "jobs.dup2",
    ]


def test_ignores_jobs_without_steps(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  empty1:\n"
        "    runs-on: ubuntu-latest\n"
        "  empty2:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_detects_duplicate_uses_only_steps(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  job1:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/setup-node@v4\n"
        "  job2:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/setup-node@v4\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.job2"
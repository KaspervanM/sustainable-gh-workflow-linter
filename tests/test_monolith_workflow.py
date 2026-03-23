from pathlib import Path

from suslint.core import lint
from suslint.rules.monolith_workflow import RULE


def test_reports_small_sequential_jobs_same_runner(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS008"
    assert issues[0].message == (
        "jobs 'build' and 'test' are small, sequential, and run on the same "
        "environment; consider merging them to reduce CI overhead"
    )
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.test"


def test_does_not_report_when_not_sequential(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_different_runner(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  test:\n"
        "    runs-on: windows-latest\n"
        "    needs: build\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_jobs_are_not_small(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: step1\n"
        "      - run: step2\n"
        "      - run: step3\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_fan_out_dependency(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  test1:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    steps:\n"
        "      - run: echo test1\n"
        "  test2:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    steps:\n"
        "      - run: echo test2\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_reports_chain_only_once_per_pair(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  a:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo a\n"
        "  b:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: a\n"
        "    steps:\n"
        "      - run: echo b\n"
        "  c:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: b\n"
        "    steps:\n"
        "      - run: echo c\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 2
    assert [i.location.trail for i in issues if i.location is not None] == [
        "jobs.b",
        "jobs.c",
    ]


def test_handles_needs_as_list(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: [build]\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.test"
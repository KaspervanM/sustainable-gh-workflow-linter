from pathlib import Path

from suslint.core import lint
from suslint.rules.shallow_clone import RULE


def test_reports_checkout_without_fetch_depth(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "      - run: echo hello\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS007"
    assert issues[0].message == "job 'build' checkout step 'steps[0]' does not use fetch-depth: 1"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build.steps[0]"
    assert issues[0].location.line == 8
    assert issues[0].location.col == 5


def test_reports_checkout_with_fetch_depth_greater_than_one(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - name: Checkout repository\n"
        "        uses: actions/checkout@v5\n"
        "        with:\n"
        "          fetch-depth: 2\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS007"
    assert issues[0].message == "job 'build' checkout step 'Checkout repository' does not use fetch-depth: 1"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build.steps[0]"


def test_does_not_report_checkout_with_fetch_depth_one_as_integer(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          fetch-depth: 1\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_checkout_with_fetch_depth_one_as_string(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          fetch-depth: '1'\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_no_checkout_step_exists(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo hello\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []
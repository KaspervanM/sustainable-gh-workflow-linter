from pathlib import Path

from suslint.core import lint
from suslint.rules.dependency_caching import RULE


def test_reports_job_that_installs_dependencies_without_cache(tmp_path: Path) -> None:
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
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS001"
    assert issues[0].message == "job 'build' installs dependencies without using dependency caching"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 5
    assert issues[0].location.col == 3


def test_does_not_report_when_setup_node_cache_is_enabled(tmp_path: Path) -> None:
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
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "          cache: npm\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_actions_cache_is_used(tmp_path: Path) -> None:
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
        "      - uses: actions/cache@v4\n"
        "        with:\n"
        "          path: ~/.cache/pip\n"
        "          key: cache-key\n"
        "      - run: pip install -r requirements.txt\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_job_has_no_dependency_installation(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  lint:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "      - run: echo hello\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []